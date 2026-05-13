from rapidfuzz import fuzz

# Fuzzy match to find similarities
def match_score(a: str, b: str) -> float:
    return (fuzz.token_set_ratio(a.lower(), b.lower()) / 100)