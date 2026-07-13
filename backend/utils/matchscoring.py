from rapidfuzz import fuzz
import logging

logger  = logging.getLogger(__name__)
# Fuzzy match to find similarities
def match_score(a: str, b: str) -> float:
    match_score= fuzz.token_set_ratio(a.lower(), b.lower()) / 100
    logger.info(f"Fuzzy match score for {a} and {b} is {match_score}")
    return (match_score)