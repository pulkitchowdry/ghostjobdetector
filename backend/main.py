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
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional
from rapidfuzz import fuzz
from core import setup_logging
import logging

# Imports from our other files
from services.ats import verify_ats
from services.description import analyze_description_quality
from services.job_recency import calculate_freshness_score
from services.applicant_ratio import calculate_applicant_ratio_score
from services.job_uniqueness import check_uniqueness
from services.community import get_community_score
from data_services.ats_details import fetch_ats_from_db

setup_logging()

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

def generate_job_hash(title: str, company: str, description: str) -> str:
    """Generate a hash for job deduplication."""
    # Normalize text
    normalized = f"{title.lower().strip()}|{company.lower().strip()}|{description[:500].lower().strip()}"
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]

# ============================================================================
# ATS Verification
# ============================================================================

# ATS_PATTERNS = {
#     "greenhouse": {
#         "url_pattern": r"boards\.greenhouse\.io/([^/]+)",
#         "api_template": "https://boards-api.greenhouse.io/v1/boards/{company}/jobs",
#     },
#     "lever": {
#         "url_pattern": r"jobs\.lever\.co/([^/]+)",
#         "api_template": "https://api.lever.co/v0/postings/{company}",
#     },
#     "workday": {
#         "url_pattern": r"([^.]+)\.wd\d+\.myworkdayjobs\.com",
#         "career_url": "https://{company}.wd5.myworkdayjobs.com/careers",
#     },
#     "ashby": {
#         "url_pattern": r"jobs\.ashbyhq\.com/([^/]+)",
#         "api_template": "https://jobs.ashbyhq.com/api/non-user-graphql",
#     },
#     "smartrecruiters" : {
#         "url_pattern": r"careers\.smartrecruiters\.com/([^/]+)",
#         "api_template": "https://careers.smartrecruiters.com/{company}/api/groups"
#     }
# }

# Company to ATS mapping (expand this in production)
COMPANY_ATS_MAP = {
    "stripe":       {
                        "ats_type": "greenhouse",
                        "ats_url_company": "stripe"
                    },
    "airbnb":       {
                        "ats_type": "greenhouse",
                        "ats_url_company": "airbnb"
                    },
    "notion":       {
                        "ats_type": "greenhouse",
                        "ats_url_company": "notion"
                    },
    "figma":        {
                        "ats_type": "lever",
                        "ats_url_company": "figma"
                    },
    "spotify":      {
                        "ats_type": "greenhouse",
                        "ats_url_company": "spotify"
                    },
    "meta":         {
                        "ats_type": "workday",
                        "ats_url_company": "meta"
                    },
    "google":       {
                        "ats_type": "workday",
                        "ats_url_company": "google"
                    },
    "freshworks":   {
                        "ats_type": "smartrecruiters",
                        "ats_url_company": "freshworks"
                    },
    "visa":         {
                        "ats_type": "smartrecruiters",
                        "ats_url_company": "visa"
                    },
    "cato networks":         {
                        "ats_type": "greenhouse",
                        "ats_url_company": "catonetworks"
                    },
}

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
    logger = logging.getLogger(__name__)
    factors = []
    insights = []
    warnings = []
    
    # Generate job ID
    job_id = generate_job_hash(request.job_title, request.company_name, request.job_description)
    
    unedited_company_name = request.company_name
    company_name = request.company_name.lower().strip()
    
    logger.info(f"un: {unedited_company_name}, cp: {company_name}")
    dummy_ats_info = fetch_ats_from_db(company_name)
    logger.info(f"dummy: {dummy_ats_info}")

    ats_info = COMPANY_ATS_MAP.get(company_name)
    logger.info(f"{ats_info}")
    if ats_info:
        ats_type = ats_info.get("ats_type")
        ats_company = ats_info.get("ats_url_company")
    else:
        ats_type, ats_company = None, None
    # 1. ATS Verification (25% weight)
    # ats_verified, ats_url, ats_details = await verify_ats(request.company_name, request.job_title)
    ats_result = await verify_ats(
            company_name=request.company_name,
            job_title=request.job_title,
            ats_type=ats_type,
            ats_company=ats_company
        )
    logger.info(f"{ats_result}")

    job_created_at = request.posted_date
    job_updated_at = None
    job_deadline = None

    if ats_result.exists is True:
        ats_score = 70 + (ats_result.confidence * 30)  # 70–100
        insights.append(
            "Job verified on company careers page with strong match confidence"
        )
        ats_details = f"Job found on the company careers page. Confidence level: {ats_score}"
        ats_verified = True
        ats_url = ats_result.url
        job_created_at = ats_result.created_at
        job_updated_at = ats_result.updated_at
        job_deadline = ats_result.application_deadline

    elif ats_result.exists is False:
        ats_score = 20 + (ats_result.confidence * 20)  # 20–40
        warnings.append(
            "Job not found on company ATS - possible ghost or repost"
        )
        ats_details = "Job not found on company careers page"
        ats_verified = False
        ats_url = None

    else:
        ats_score = 50  # unknown / unverifiable
        warnings.append(
            "ATS verification inconclusive - could not confirm listing"
        )
        ats_details = "Company careers page verification was inconclusive."
        ats_verified = None
        ats_url = None
    
    logger.info(f"{ats_score}")
    factors.append(AnalysisFactor(
        name="ATS Verification",
        score=round(ats_score),
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
        name="Job Description Quality",
        score=desc_score,
        weight=0.20,
        details=f"Analyzed for specificity and red flags",
        indicators=desc_indicators
    ))
    
    # 3. Posting Freshness (15% weight)
    logger.info(f"created_at: {job_created_at}")
    freshness_score, days_ago, freshness_details = calculate_freshness_score(job_created_at)
    
    if freshness_score >= 80:
        insights.append("Recently posted - good sign of active hiring")
    elif freshness_score < 40:
        warnings.append("Posting is quite old - may no longer be active")
    
    factors.append(AnalysisFactor(
        name="Job Posting Recency",
        score=freshness_score,
        weight=0.15,
        details=freshness_details,
        indicators=[]
    ))
    
    # 4. Applicant Ratio (10% weight)
    applicant_score, applicant_details = calculate_applicant_ratio_score(
        request.applicant_count, job_created_at
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
