import logging
import re

from .description_dictionary import GENERIC_PHRASES, SPECIFIC_INDICATORS, RED_FLAGS
from .role_taxonomy import compute_role_relevance

logger = logging.getLogger(__name__)

# Below this relevance score (and only when the classifier is confident),
# we treat it as a hard signal that content doesn't belong to this posting
# at all, and cap the score regardless of how "specific" the text looks.
HARD_MISMATCH_THRESHOLD = 20
HARD_MISMATCH_CAP = 15


def _analyze_structural_quality(description: str) -> tuple[int, list[str]]:
    """The original regex/keyword scoring - checks the description in
    isolation (length, structure, buzzwords, red flags). This has no way
    to know whether the content actually belongs to the stated job title;
    that's handled separately by role_taxonomy.compute_role_relevance."""
    text = description.lower()
    indicators = []

    words = text.split()
    word_count = len(words)

    generic_hits = sum(1 for phrase in GENERIC_PHRASES if phrase in text)
    generic_score = min(generic_hits * 2, 20)

    tech_hits = sum(1 for pattern in SPECIFIC_INDICATORS if re.search(pattern, text, re.IGNORECASE))
    specific_score = min(tech_hits * 5, 40)

    red_flags = sum(1 for pattern in RED_FLAGS if re.search(pattern, text, re.IGNORECASE))
    red_flag_score = red_flags * 15

    structure_score = 0
    for section in ["responsibilities", "requirements", "qualifications"]:
        if section in text:
            structure_score += 10

    filler_ratio = generic_hits / max(word_count, 1)
    filler_penalty = int(filler_ratio * 30)

    if word_count < 80:
        length_score = -10
        indicators.append("Very short description")
    elif word_count > 250:
        length_score = 10
    else:
        length_score = 0

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

    indicators.append(f"Generic phrases: {generic_hits}")
    indicators.append(f"Specific signals: {tech_hits}")
    indicators.append(f"Red flags: {red_flags}")

    return score, indicators


def analyze_description_quality(description: str, job_title: str | None = None) -> tuple[int, list[str]]:
    """
    Two independent checks, combined:
      1. Structural quality - is the writing specific/detailed vs generic/thin?
      2. Title/content relevance - does the content actually match the stated
         role? (catches e.g. a "Software Engineer" title paired with a food-
         service description, which pure regex on the description alone
         cannot detect.)

    A confident, strong relevance mismatch acts as a hard cap on the final
    score - it's a stronger fraud signal than "vague but on-topic", so it
    shouldn't just quietly average out against a high structural score.
    """
    structural_score, indicators = _analyze_structural_quality(description)

    if not job_title:
        return structural_score, indicators

    relevance = compute_role_relevance(job_title, description)
    indicators.append(
        f"Title/content relevance: {relevance['relevance_score']}/100 - {relevance['reason']}"
    )

    if relevance["confident"] and relevance["relevance_score"] <= HARD_MISMATCH_THRESHOLD:
        final_score = min(structural_score, HARD_MISMATCH_CAP)
        indicators.append(
            "MISMATCH: description content does not appear to match the stated job title"
        )
    else:
        # Soft blend otherwise - relevance nudges the score without a
        # confident classification overriding everything else.
        final_score = int(round(structural_score * 0.7 + relevance["relevance_score"] * 0.3))

    final_score = max(0, min(100, final_score))
    logger.info(
        f"description_score: structural={structural_score} "
        f"relevance={relevance['relevance_score']} final={final_score}"
    )

    return final_score, indicators