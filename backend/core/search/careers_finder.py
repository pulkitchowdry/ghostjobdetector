from ddgs import DDGS
from urllib.parse import urlparse
import logging
from core.constants.ats_patterns import ATS_PATTERNS, CAREERS_KEYWORDS, BAD_DOMAINS

logger = logging.getLogger(__name__)

def detect_ats(url: str) -> dict | None:
    url_l = url.lower()

    for ats, pattern in ATS_PATTERNS.items():
        if pattern in url_l:
            logger.debug(f"ATS detected: {ats} in {url}")
            return {
                "ats_name": ats,
                "ats_base_url": pattern
            }

    return None

from urllib.parse import urlparse

def score_url(url: str, company_name: str) -> int:
    url_l = url.lower()
    parsed = urlparse(url)

    domain = parsed.netloc.lower()
    path = parsed.path.lower()

    score = 0

    company_slug = company_name.lower().replace(" ", "")

    # 3. Direct ats link
    ATS_PATTERNS = {
        "greenhouse": "boards.greenhouse.io",
        "lever": "jobs.lever.co",
        "workday": "myworkdayjobs.com",
        "smartrecruiters": "smartrecruiters.com",
    }

    for ats, pattern in ATS_PATTERNS.items():
        if pattern in url_l:
            score += 300

    # 2. Subdomain as careers
    if domain.startswith("careers.") or domain.startswith("jobs."):
        if company_slug in domain:
            score += 200

    # 3. Domain plus careers path
    if company_slug in domain.replace("-", "").replace(".", ""):
        if any(x in path for x in ["/careers", "/jobs", "/work", "/hiring"]):
            score += 200

    # 4. generic careers intent
    if any(x in path for x in ["careers", "jobs", "join", "hiring"]):
        score += 50

    # 5. penalty for spam / SEO sites
    BAD_DOMAINS = [
        "medium.com",
        "quora.com",
        "reddit.com",
        "bestbuyideas.com",
        "blogspot.com",
    ]

    if any(bad in domain for bad in BAD_DOMAINS):
        score -= 250

    return score

def find_careers_page(company_name: str) -> dict | None:
    logger.info(f"Searching careers page for: {company_name}")

    queries = [
        f"{company_name} careers",
    ]

    results = []

    with DDGS() as ddgs:
        for q in queries:
            logger.info(f"Querying DDG: {q}")

            for r in ddgs.text(q, max_results=10):
                url = (r.get("href") or r.get("url") or "").strip()

                if not url:
                    logger.debug(f"Skipping empty result: {r}")
                    continue

                domain = urlparse(url).netloc.lower()

                logger.debug(f"Found URL: {url}")

                # filter bad domains
                if any(bad in domain for bad in BAD_DOMAINS):
                    logger.debug(f"Filtered bad domain: {domain}")
                    continue

                results.append(url)

    logger.info(f"DDG results count: {len(results)}")

    if not results:
        logger.warning(f"No results found for {company_name}")
        return None

    scored = [(url, score_url(url, company_name)) for url in results]
    scored.sort(key=lambda x: x[1], reverse=True)

    logger.info("Top 5 scored results:")
    for url, score in scored[:5]:
        logger.info(f"{score:4} -> {url}")

    best_url = scored[0][0]
    best_score = scored[0][1]

    logger.info(f"Best URL selected: {best_url} (score={best_score})")

    ats = detect_ats(best_url)
    logger.info(f"ATS detected: {ats}")

    return {
        "careers_url": best_url,
        "ats": ats,
    }