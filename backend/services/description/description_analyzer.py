import logging
import re
import math
from .description_dictionary import GENERIC_PHRASES, SPECIFIC_INDICATORS, RED_FLAGS

def analyze_description_quality(description: str) -> tuple[int, list[str]]:
    logger = logging.getLogger(__name__)
    text = description.lower()
    indicators = []

    words = text.split()
    word_count = len(words)

    # ---------------------------
    # 1. Generic signal (weak penalty)
    # ---------------------------
    generic_hits = sum(1 for phrase in GENERIC_PHRASES if phrase in text)
    generic_score = min(generic_hits * 2, 20)

    logger.info(f"generic_hits: {generic_hits}, generic_score: {generic_score}")
    # ---------------------------
    # 2. Specific signal (strong reward)
    # ---------------------------
    tech_hits = sum(
        1 for pattern in SPECIFIC_INDICATORS
        if re.search(pattern, text, re.IGNORECASE)
    )
    specific_score = min(tech_hits * 5, 40)

    logger.info(f"tech_hits: {tech_hits}")
    # ---------------------------
    # 3. Red flags (strong penalty)
    # ---------------------------
    red_flags = sum(
        1 for pattern in RED_FLAGS
        if re.search(pattern, text, re.IGNORECASE)
    )
    red_flag_score = red_flags * 15
    logger.info(f"red_flag: {red_flag_score}")
    # ---------------------------
    # 4. Structure score
    # ---------------------------
    structure_score = 0
    for section in ["responsibilities", "requirements", "qualifications"]:
        if section in text:
            structure_score += 10

    logger.info(f"struc: {structure_score}")
    # ---------------------------
    # 5. Filler ratio
    # ---------------------------
    filler_words = generic_hits
    filler_ratio = filler_words / max(word_count, 1)

    filler_penalty = int(filler_ratio * 30)
    logger.info(f"filler: {filler_penalty}")

    # ---------------------------
    # 6. Length signal
    # ---------------------------
    if word_count < 80:
        length_score = -10
        indicators.append("Very short description")
    elif word_count > 250:
        length_score = 10
    else:
        length_score = 0

    logger.info(f"len: {length_score}")
    # ---------------------------
    # FINAL SCORE
    # ---------------------------
    score = (
        50
        + specific_score
        + structure_score
        - generic_score
        - red_flag_score
        - filler_penalty
        + length_score
    )

    score = max(0, min(100, score))
    logger.info(f"description_score: {score}")

    indicators.append(f"Generic phrases: {generic_hits}")
    indicators.append(f"Specific signals: {tech_hits}")
    indicators.append(f"Red flags: {red_flags}")

    return score, indicators


# Old one
# def analyze_description_quality(description: str) -> tuple[int, list[str]]:
#     """
#     Analyze job description for specificity vs generic content.
#     Returns score (0-100) and list of indicators found.
#     """
#     description_lower = description.lower()
#     indicators = []
    
#     # Count generic phrases (decreases score)
#     generic_count = sum(1 for phrase in GENERIC_PHRASES if phrase in description_lower)
    
#     # Count specific indicators (increases score)
#     specific_count = 0
#     for pattern in SPECIFIC_INDICATORS:
#         matches = re.findall(pattern, description_lower, re.IGNORECASE)
#         if matches:
#             specific_count += len(matches)
#             indicators.append(f"Found specific detail: {pattern[:30]}...")
    
#     # Check for red flags
#     red_flag_count = 0
#     for pattern in RED_FLAGS:
#         if re.search(pattern, description_lower, re.IGNORECASE):
#             red_flag_count += 1
#             indicators.append(f"Warning: Red flag pattern detected")
    
#     # Description length analysis
#     word_count = len(description.split())
#     if word_count < 100:
#         indicators.append("Very short description (under 100 words)")
#     elif word_count > 300:
#         indicators.append("Detailed description (300+ words)")
    
#     # Calculate score
#     # Start at 50, adjust based on findings
#     base_score = 50
    
#     # Penalize generic content (-3 per generic phrase, max -30)
#     generic_penalty = min(generic_count * 3, 30)
    
#     # Reward specific content (+5 per specific indicator, max +40)
#     specific_bonus = min(specific_count * 5, 40)
    
#     # Penalize red flags heavily (-15 per flag)
#     red_flag_penalty = red_flag_count * 15
    
#     # Length bonus/penalty
#     length_modifier = 0
#     if word_count < 100:
#         length_modifier = -10
#     elif word_count > 300:
#         length_modifier = 10
    
#     score = base_score - generic_penalty + specific_bonus - red_flag_penalty + length_modifier
#     score = max(0, min(100, score))
    
#     return score, indicators