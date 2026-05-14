import math
from collections import defaultdict

def get_community_score(job_id: str) -> tuple[int, dict]:
    """
    Calculate score based on community reports.
    """
    #dummy
    community_reports: dict[str, list[dict]] = defaultdict(list)
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