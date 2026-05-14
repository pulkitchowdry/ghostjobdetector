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