"""
Ghost Job Detector - FastAPI Backend
Provides NLP-based analysis and scoring for job postings
"""

import fastapi
import fastapi.middleware.cors
from pydantic import BaseModel, Field
from typing import Optional
import re
import math
from datetime import datetime, timedelta
import hashlib
import httpx
from collections import defaultdict

app = fastapi.FastAPI(
    title="Ghost Job Detector API",
    description="Analyze job postings for legitimacy indicators",
    version="1.0.0"
)

app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# In-Memory Storage (Replace with Redis/Supabase in production)
# ============================================================================

# Cache for ATS verification results
ats_cache: dict[str, dict] = {}

# Community reports storage
community_reports: dict[str, list[dict]] = defaultdict(list)

# Job posting history for duplicate detection
job_history: dict[str, dict] = {}

# ============================================================================
# Pydantic Models
# ============================================================================

class JobAnalysisRequest(BaseModel):
    job_title: str = Field(..., description="Job title")
    company_name: str = Field(..., description="Company name")
    job_description: str = Field(..., description="Full job description text")
    posted_date: Optional[str] = Field(None, description="When the job was posted (ISO format or relative like '2 weeks ago')")
    applicant_count: Optional[int] = Field(None, description="Number of applicants")
    job_url: Optional[str] = Field(None, description="URL of the job posting")
    location: Optional[str] = Field(None, description="Job location")

class CommunityReport(BaseModel):
    job_id: str = Field(..., description="Unique job identifier")
    report_type: str = Field(..., description="Type: interview_scheduled, response_received, no_response, offer_received")
    fingerprint: Optional[str] = Field(None, description="Anonymous user fingerprint for spam prevention")
    comment: Optional[str] = Field(None, max_length=500)

class AnalysisFactor(BaseModel):
    name: str
    score: int
    weight: float
    details: str
    indicators: list[str]

class AnalysisResponse(BaseModel):
    legitimacy_score: int = Field(..., ge=0, le=100)
    verdict: str
    job_id: str
    factors: list[AnalysisFactor]
    insights: list[str]
    warnings: list[str]
    ats_verified: Optional[bool]
    ats_url: Optional[str]
    community_stats: dict

# ============================================================================
# NLP Analysis Functions (Heuristic-based, production-ready without ML deps)
# ============================================================================

# Generic phrases commonly found in ghost jobs
GENERIC_PHRASES = [
    "fast-paced environment",
    "team player",
    "self-starter",
    "detail-oriented",
    "excellent communication skills",
    "ability to multitask",
    "results-driven",
    "dynamic environment",
    "competitive salary",
    "great benefits",
    "exciting opportunity",
    "growing company",
    "passionate about",
    "rock star",
    "ninja",
    "guru",
    "synergy",
    "leverage",
    "paradigm",
    "best in class",
]

# Specific indicators of real jobs
SPECIFIC_INDICATORS = [
    r"\d+\s*\+?\s*years?\s*(of\s+)?experience",  # Years of experience
    r"\$\d+[kK]?\s*[-–]\s*\$?\d+[kK]?",  # Salary range
    r"[A-Z][a-z]+\s+[A-Z][a-z]+",  # Proper names (hiring manager, etc.)
    r"(python|java|javascript|typescript|react|node|aws|gcp|azure|kubernetes|docker)",  # Tech stack
    r"(bachelor|master|phd|degree)\s*(in|'s)?",  # Education requirements
    r"report(ing)?\s+to",  # Reporting structure
    r"team\s+of\s+\d+",  # Team size
    r"(q[1-4]|quarter|fiscal)",  # Business timing
    r"(series\s+[a-z]|seed|funding)",  # Funding stage
]

# Red flag patterns
RED_FLAGS = [
    r"immediate\s+(start|hire|opening)",
    r"urgent(ly)?\s+(need|hiring|fill)",
    r"asap",
    r"no\s+experience\s+(needed|required|necessary)",
    r"unlimited\s+earning",
    r"work\s+from\s+home.*\$\d{4,}",
    r"be\s+your\s+own\s+boss",
]

def analyze_description_quality(description: str) -> tuple[int, list[str]]:
    """
    Analyze job description for specificity vs generic content.
    Returns score (0-100) and list of indicators found.
    """
    description_lower = description.lower()
    indicators = []
    
    # Count generic phrases (decreases score)
    generic_count = sum(1 for phrase in GENERIC_PHRASES if phrase in description_lower)
    
    # Count specific indicators (increases score)
    specific_count = 0
    for pattern in SPECIFIC_INDICATORS:
        matches = re.findall(pattern, description_lower, re.IGNORECASE)
        if matches:
            specific_count += len(matches)
            indicators.append(f"Found specific detail: {pattern[:30]}...")
    
    # Check for red flags
    red_flag_count = 0
    for pattern in RED_FLAGS:
        if re.search(pattern, description_lower, re.IGNORECASE):
            red_flag_count += 1
            indicators.append(f"Warning: Red flag pattern detected")
    
    # Description length analysis
    word_count = len(description.split())
    if word_count < 100:
        indicators.append("Very short description (under 100 words)")
    elif word_count > 300:
        indicators.append("Detailed description (300+ words)")
    
    # Calculate score
    # Start at 50, adjust based on findings
    base_score = 50
    
    # Penalize generic content (-3 per generic phrase, max -30)
    generic_penalty = min(generic_count * 3, 30)
    
    # Reward specific content (+5 per specific indicator, max +40)
    specific_bonus = min(specific_count * 5, 40)
    
    # Penalize red flags heavily (-15 per flag)
    red_flag_penalty = red_flag_count * 15
    
    # Length bonus/penalty
    length_modifier = 0
    if word_count < 100:
        length_modifier = -10
    elif word_count > 300:
        length_modifier = 10
    
    score = base_score - generic_penalty + specific_bonus - red_flag_penalty + length_modifier
    score = max(0, min(100, score))
    
    return score, indicators

def calculate_freshness_score(posted_date: Optional[str]) -> tuple[int, str]:
    """
    Calculate score based on posting age.
    Newer posts score higher.
    """
    if not posted_date:
        return 50, "Posting date unknown"
    
    # Parse relative dates like "2 weeks ago", "3 days ago"
    posted_date_lower = posted_date.lower()
    days_ago = None
    
    # Try parsing relative dates
    if "just now" in posted_date_lower or "today" in posted_date_lower:
        days_ago = 0
    elif "yesterday" in posted_date_lower:
        days_ago = 1
    elif match := re.search(r"(\d+)\s*(day|hour|minute)s?\s*ago", posted_date_lower):
        num = int(match.group(1))
        unit = match.group(2)
        if unit == "hour" or unit == "minute":
            days_ago = 0
        else:
            days_ago = num
    elif match := re.search(r"(\d+)\s*week", posted_date_lower):
        days_ago = int(match.group(1)) * 7
    elif match := re.search(r"(\d+)\s*month", posted_date_lower):
        days_ago = int(match.group(1)) * 30
    
    # Try ISO date parsing
    if days_ago is None:
        try:
            posted = datetime.fromisoformat(posted_date.replace("Z", "+00:00"))
            days_ago = (datetime.now(posted.tzinfo) - posted).days
        except:
            return 50, "Could not parse posting date"
    
    # Score calculation with decay
    # 0-7 days: 100-85
    # 7-14 days: 85-70
    # 14-30 days: 70-50
    # 30-60 days: 50-30
    # 60+ days: 30-10
    
    if days_ago <= 7:
        score = 100 - (days_ago * 2)
    elif days_ago <= 14:
        score = 85 - ((days_ago - 7) * 2)
    elif days_ago <= 30:
        score = 70 - ((days_ago - 14) * 1.25)
    elif days_ago <= 60:
        score = 50 - ((days_ago - 30) * 0.67)
    else:
        score = max(10, 30 - ((days_ago - 60) * 0.2))
    
    return int(score), f"Posted {days_ago} days ago"

def calculate_applicant_ratio_score(applicant_count: Optional[int], posted_date: Optional[str]) -> tuple[int, str]:
    """
    Analyze applicant count relative to posting age.
    Very high applicants on old posts = potential ghost job.
    """
    if applicant_count is None:
        return 50, "Applicant count unknown"
    
    # Get days since posting
    freshness_score, details = calculate_freshness_score(posted_date)
    
    # Extract days from details
    days_match = re.search(r"(\d+)\s*days?\s*ago", details)
    days_ago = int(days_match.group(1)) if days_match else 14  # Default assumption
    
    if days_ago == 0:
        days_ago = 1  # Avoid division by zero
    
    # Calculate applicants per day
    applicants_per_day = applicant_count / days_ago
    
    # Scoring logic
    # Normal: 10-50 applicants/day for popular roles
    # Suspicious: 100+ applicants/day on old posts
    
    if applicant_count < 50 and days_ago < 7:
        score = 90  # New post, reasonable applicants
        detail = "Reasonable applicant count for new posting"
    elif applicant_count < 200 and days_ago < 14:
        score = 75
        detail = "Normal applicant volume"
    elif applicant_count > 500 and days_ago > 30:
        score = 30
        detail = "Very high applicants on old posting"
    elif applicant_count > 1000:
        score = 20
        detail = "Extremely high applicant count - may indicate stale listing"
    else:
        # Linear interpolation
        score = max(20, 80 - (applicant_count / 20))
        detail = f"{applicant_count} applicants over {days_ago} days"
    
    return int(score), detail

def generate_job_hash(title: str, company: str, description: str) -> str:
    """Generate a hash for job deduplication."""
    # Normalize text
    normalized = f"{title.lower().strip()}|{company.lower().strip()}|{description[:500].lower().strip()}"
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]

def check_uniqueness(job_hash: str, company: str, description: str) -> tuple[int, list[str]]:
    """
    Check if job appears to be reposted or duplicated.
    """
    indicators = []
    similar_count = 0
    
    # Check against job history
    for stored_hash, stored_job in job_history.items():
        if stored_hash == job_hash:
            similar_count += 1
            indicators.append(f"Exact duplicate found from {stored_job.get('first_seen', 'unknown date')}")
        elif stored_job.get("company", "").lower() == company.lower():
            # Same company, check description similarity (simple word overlap)
            stored_words = set(stored_job.get("description", "").lower().split())
            current_words = set(description.lower().split())
            
            if len(stored_words) > 0 and len(current_words) > 0:
                overlap = len(stored_words & current_words) / max(len(stored_words), len(current_words))
                if overlap > 0.7:
                    similar_count += 1
                    indicators.append("Very similar posting found from same company")
    
    # Score based on findings
    if similar_count == 0:
        score = 100
        indicators.append("No duplicate postings detected")
    elif similar_count == 1:
        score = 70
    elif similar_count == 2:
        score = 50
    else:
        score = 30
        indicators.append(f"Found {similar_count} similar/duplicate postings")
    
    return score, indicators

def get_community_score(job_id: str) -> tuple[int, dict]:
    """
    Calculate score based on community reports.
    """
    reports = community_reports.get(job_id, [])
    
    if not reports:
        return 50, {"total_reports": 0, "interview_scheduled": 0, "response_received": 0, "no_response": 0, "offer_received": 0}
    
    # Count report types
    counts = {
        "interview_scheduled": 0,
        "response_received": 0,
        "no_response": 0,
        "offer_received": 0,
    }
    
    for report in reports:
        report_type = report.get("report_type", "")
        if report_type in counts:
            counts[report_type] += 1
    
    counts["total_reports"] = len(reports)
    
    # Calculate score
    positive = counts["interview_scheduled"] + counts["response_received"] + (counts["offer_received"] * 2)
    negative = counts["no_response"]
    
    total = positive + negative
    if total == 0:
        return 50, counts
    
    # Weighted score
    score = int((positive / total) * 100)
    
    # Boost if we have offers
    if counts["offer_received"] > 0:
        score = min(100, score + 10)
    
    return score, counts

# ============================================================================
# ATS Verification
# ============================================================================

ATS_PATTERNS = {
    "greenhouse": {
        "url_pattern": r"boards\.greenhouse\.io/([^/]+)",
        "api_template": "https://boards-api.greenhouse.io/v1/boards/{company}/jobs",
    },
    "lever": {
        "url_pattern": r"jobs\.lever\.co/([^/]+)",
        "api_template": "https://api.lever.co/v0/postings/{company}",
    },
    "workday": {
        "url_pattern": r"([^.]+)\.wd\d+\.myworkdayjobs\.com",
        "career_url": "https://{company}.wd5.myworkdayjobs.com/careers",
    },
    "ashby": {
        "url_pattern": r"jobs\.ashbyhq\.com/([^/]+)",
        "api_template": "https://jobs.ashbyhq.com/api/non-user-graphql",
    },
}

# Company to ATS mapping (expand this in production)
COMPANY_ATS_MAP = {
    "stripe": ("greenhouse", "stripe"),
    "airbnb": ("greenhouse", "airbnb"),
    "notion": ("greenhouse", "notion"),
    "figma": ("lever", "figma"),
    "spotify": ("greenhouse", "spotify"),
    "meta": ("workday", "meta"),
    "google": ("workday", "google"),
}

async def verify_ats(company_name: str, job_title: str) -> tuple[bool, Optional[str], str]:
    """
    Attempt to verify if job exists on company's ATS.
    Returns (verified, ats_url, details)
    """
    company_lower = company_name.lower().strip()
    
    # Check cache first
    cache_key = f"{company_lower}:{job_title.lower()[:50]}"
    if cache_key in ats_cache:
        cached = ats_cache[cache_key]
        return cached["verified"], cached.get("url"), "Retrieved from cache"
    
    # Try known company mappings
    if company_lower in COMPANY_ATS_MAP:
        ats_type, ats_company = COMPANY_ATS_MAP[company_lower]
        
        if ats_type == "greenhouse":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    url = f"https://boards-api.greenhouse.io/v1/boards/{ats_company}/jobs"
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        jobs = response.json().get("jobs", [])
                        job_title_lower = job_title.lower()
                        
                        for job in jobs:
                            if job_title_lower in job.get("title", "").lower():
                                ats_url = f"https://boards.greenhouse.io/{ats_company}"
                                ats_cache[cache_key] = {"verified": True, "url": ats_url}
                                return True, ats_url, "Job found on company Greenhouse careers page"
                        
                        ats_cache[cache_key] = {"verified": False}
                        return False, None, "Job not found on company Greenhouse - may be filled or removed"
            except Exception as e:
                return None, None, f"Could not verify ATS: {str(e)}"
        
        elif ats_type == "lever":
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    url = f"https://api.lever.co/v0/postings/{ats_company}"
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        jobs = response.json()
                        job_title_lower = job_title.lower()
                        
                        for job in jobs:
                            if job_title_lower in job.get("text", "").lower():
                                ats_url = f"https://jobs.lever.co/{ats_company}"
                                ats_cache[cache_key] = {"verified": True, "url": ats_url}
                                return True, ats_url, "Job found on company Lever careers page"
                        
                        ats_cache[cache_key] = {"verified": False}
                        return False, None, "Job not found on company Lever - may be filled or removed"
            except Exception as e:
                return None, None, f"Could not verify ATS: {str(e)}"
    
    # For unknown companies, return None (unverifiable)
    return None, None, "ATS verification not available for this company"

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ghost-job-detector"}

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_job(request: JobAnalysisRequest) -> AnalysisResponse:
    """
    Analyze a job posting and return legitimacy score with detailed breakdown.
    """
    factors = []
    insights = []
    warnings = []
    
    # Generate job ID
    job_id = generate_job_hash(request.job_title, request.company_name, request.job_description)
    
    # 1. ATS Verification (25% weight)
    ats_verified, ats_url, ats_details = await verify_ats(request.company_name, request.job_title)
    
    if ats_verified is True:
        ats_score = 100
        insights.append("Job verified on company careers page - strong legitimacy signal")
    elif ats_verified is False:
        ats_score = 30
        warnings.append("Job not found on company ATS - verify directly with company")
    else:
        ats_score = 50  # Unable to verify
    
    factors.append(AnalysisFactor(
        name="ATS Verification",
        score=ats_score,
        weight=0.25,
        details=ats_details,
        indicators=["Checked against known ATS systems"]
    ))
    
    # 2. Description Quality (20% weight)
    desc_score, desc_indicators = analyze_description_quality(request.job_description)
    
    if desc_score >= 70:
        insights.append("Job description contains specific, detailed requirements")
    elif desc_score < 40:
        warnings.append("Job description appears generic - may lack real requirements")
    
    factors.append(AnalysisFactor(
        name="Description Quality",
        score=desc_score,
        weight=0.20,
        details=f"Analyzed for specificity and red flags",
        indicators=desc_indicators
    ))
    
    # 3. Posting Freshness (15% weight)
    freshness_score, freshness_details = calculate_freshness_score(request.posted_date)
    
    if freshness_score >= 80:
        insights.append("Recently posted - good sign of active hiring")
    elif freshness_score < 40:
        warnings.append("Posting is quite old - may no longer be active")
    
    factors.append(AnalysisFactor(
        name="Posting Freshness",
        score=freshness_score,
        weight=0.15,
        details=freshness_details,
        indicators=[]
    ))
    
    # 4. Applicant Ratio (10% weight)
    applicant_score, applicant_details = calculate_applicant_ratio_score(
        request.applicant_count, request.posted_date
    )
    
    if applicant_score < 40:
        warnings.append("High applicant count relative to posting age")
    
    factors.append(AnalysisFactor(
        name="Applicant Ratio",
        score=applicant_score,
        weight=0.10,
        details=applicant_details,
        indicators=[]
    ))
    
    # 5. Uniqueness Check (15% weight)
    uniqueness_score, uniqueness_indicators = check_uniqueness(
        job_id, request.company_name, request.job_description
    )
    
    # Store in job history for future checks
    job_history[job_id] = {
        "title": request.job_title,
        "company": request.company_name,
        "description": request.job_description[:500],
        "first_seen": datetime.now().isoformat(),
    }
    
    if uniqueness_score < 50:
        warnings.append("Similar postings detected - may be repeatedly reposted")
    
    factors.append(AnalysisFactor(
        name="Uniqueness",
        score=uniqueness_score,
        weight=0.15,
        details="Checked for duplicate/reposted listings",
        indicators=uniqueness_indicators
    ))
    
    # 6. Community Reports (15% weight)
    community_score, community_stats = get_community_score(job_id)
    
    if community_stats["total_reports"] > 0:
        if community_stats["interview_scheduled"] > 0 or community_stats["offer_received"] > 0:
            insights.append(f"Community reports indicate active hiring ({community_stats['interview_scheduled']} interviews, {community_stats['offer_received']} offers)")
        if community_stats["no_response"] > community_stats["response_received"] + community_stats["interview_scheduled"]:
            warnings.append("More no-response reports than positive outcomes")
    
    factors.append(AnalysisFactor(
        name="Community Signals",
        score=community_score,
        weight=0.15,
        details=f"{community_stats['total_reports']} community reports",
        indicators=[
            f"{community_stats['interview_scheduled']} interviews scheduled",
            f"{community_stats['response_received']} responses received",
            f"{community_stats['no_response']} no responses",
            f"{community_stats['offer_received']} offers received",
        ]
    ))
    
    # Calculate weighted total score
    total_score = sum(f.score * f.weight for f in factors)
    legitimacy_score = int(round(total_score))
    
    # Determine verdict
    if legitimacy_score >= 80:
        verdict = "highly_legitimate"
    elif legitimacy_score >= 60:
        verdict = "mostly_positive"
    elif legitimacy_score >= 40:
        verdict = "mixed_signals"
    elif legitimacy_score >= 20:
        verdict = "multiple_warnings"
    else:
        verdict = "likely_ghost_job"
    
    return AnalysisResponse(
        legitimacy_score=legitimacy_score,
        verdict=verdict,
        job_id=job_id,
        factors=factors,
        insights=insights,
        warnings=warnings,
        ats_verified=ats_verified,
        ats_url=ats_url,
        community_stats=community_stats,
    )

@app.post("/report")
async def submit_report(report: CommunityReport) -> dict:
    """
    Submit a community report for a job posting.
    """
    valid_types = ["interview_scheduled", "response_received", "no_response", "offer_received"]
    
    if report.report_type not in valid_types:
        raise fastapi.HTTPException(
            status_code=400,
            detail=f"Invalid report type. Must be one of: {valid_types}"
        )
    
    # Simple spam prevention - limit reports per fingerprint
    if report.fingerprint:
        existing_reports = community_reports.get(report.job_id, [])
        same_fingerprint = [r for r in existing_reports if r.get("fingerprint") == report.fingerprint]
        
        if len(same_fingerprint) >= 3:
            raise fastapi.HTTPException(
                status_code=429,
                detail="Too many reports from this device for this job"
            )
    
    # Store the report
    community_reports[report.job_id].append({
        "report_type": report.report_type,
        "fingerprint": report.fingerprint,
        "comment": report.comment,
        "timestamp": datetime.now().isoformat(),
    })
    
    return {"status": "success", "message": "Report submitted successfully"}

@app.get("/reports/{job_id}")
async def get_reports(job_id: str) -> dict:
    """
    Get community reports for a job posting.
    """
    reports = community_reports.get(job_id, [])
    
    # Count by type
    counts = {
        "interview_scheduled": 0,
        "response_received": 0,
        "no_response": 0,
        "offer_received": 0,
    }
    
    for report in reports:
        if report["report_type"] in counts:
            counts[report["report_type"]] += 1
    
    return {
        "job_id": job_id,
        "total_reports": len(reports),
        "breakdown": counts,
        "recent_comments": [
            r.get("comment") for r in reports[-5:] if r.get("comment")
        ]
    }

@app.get("/stats")
async def get_stats() -> dict:
    """
    Get overall platform statistics.
    """
    total_jobs = len(job_history)
    total_reports = sum(len(reports) for reports in community_reports.values())
    
    return {
        "total_jobs_analyzed": total_jobs,
        "total_community_reports": total_reports,
        "cached_ats_results": len(ats_cache),
    }
