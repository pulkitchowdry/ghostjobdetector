import math
import re
from services.job_recency import calculate_freshness_score
from typing import Optional

def calculate_applicant_ratio_score(applicant_count: Optional[int], posted_date: Optional[str]) -> tuple[int, str]:
    """
    Analyze applicant count relative to posting age.
    Very high applicants on old posts = potential ghost job.
    """
    if applicant_count is None:
        return 50, "Applicant count unknown"
    
    # Get days since posting
    freshness_score, days_ago, details = calculate_freshness_score(posted_date)
    
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