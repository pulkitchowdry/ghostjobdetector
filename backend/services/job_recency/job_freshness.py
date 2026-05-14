import math
from typing import Optional
import re
import logging
from datetime import datetime

def calculate_freshness_score(posted_date: Optional[str]) -> tuple[int, int, str]:
    """
    Calculate score based on posting age.
    Newer posts score higher.
    """
    logger = logging.getLogger(__name__)
    if not posted_date:
        return 50, None, "Posting date unknown"
    
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

    logger.info(f"days_ago: {days_ago}")
    # Try ISO date parsing
    if days_ago is None:
        try:
            posted = datetime.fromisoformat(posted_date.replace("Z", "+00:00"))
            logger.info(f"posted: {posted}")
            days_ago = (datetime.now(posted.tzinfo) - posted).days
            logger.info(f"parsed from date: {days_ago}")
        except Exception as err:
            logger.exception(f"Could not parse posting date {err}")
            return 50, None, "Could not parse posting date"
    
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
    
    return int(score), int(days_ago), f"Posted {days_ago} days ago"