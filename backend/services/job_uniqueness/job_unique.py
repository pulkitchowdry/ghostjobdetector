import logging
import math

def check_uniqueness(job_hash: str, company: str, description: str) -> tuple[int, list[str]]:
    """
    Check if job appears to be reposted or duplicated.
    """
    indicators = []
    similar_count = 0
    
    # Check against job history
    #dummy
    job_history: dict[str, dict] = {}
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