from core.db import supabase
from core.search.careers_finder import find_careers_page
import logging
from core.constants.ats_patterns import ATS_PATTERNS
import httpx

logger = logging.getLogger(__name__)

def classify_url(url: str) -> str:
    url_l = url.lower()

    if any(p in url_l for p in ATS_PATTERNS):
        return "ats"

    path = urlparse(url).path.lower()

    if any(x in path for x in ["careers", "jobs", "hiring", "work-with-us"]):
        return "careers"

    return "unknown"

def detect_ats_from_url(url: str) -> dict | None:
    url_l = url.lower()

    for name, pattern in ATS_PATTERNS.items():
        if pattern in url_l:
            return {
                "ats_name": name,
                "ats_url": pattern
            }

    return None

def detect_ats_from_html(html: str) -> dict | None:
    html_l = html.lower()

    for name, pattern in ATS_PATTERNS.items():
        if pattern in html_l:
            return {
                "ats_name": name,
                "ats_url": pattern
            }

    return None

def fetch_new_company_ats(company_name: str) -> dict:
    logger = logging.getLogger(__name__)

    best = find_careers_page(company_name)

    if not best:
        logger.warning("No careers page found")
        return {"ats_name": None, "ats_url": None}

    url = best["careers_url"]
    logger.info(f"Best careers URL: {url}")

    # =========================
    # CASE 1: direct ATS link
    # =========================
    ats = detect_ats_from_url(url)
    if ats:
        logger.info(f"Direct ATS found: {ats}")
        return ats

    # =========================
    # CASE 2: inspect careers page
    # =========================
    try:
        html = httpx.get(url, timeout=10).text
        ats = detect_ats_from_html(html)

        if ats:
            logger.info(f"Embedded ATS found: {ats}")
            return ats

    except Exception as e:
        logger.error(f"Failed to fetch page: {e}")

    # =========================
    # CASE 3: nothing found
    # =========================
    logger.info("No ATS detected")
    return {"ats_name": None, "ats_url": None}

def fetch_ats_from_db(company_name: str) -> dict:
    company_info = (
        supabase.table("companies")
                .select("id")
                .eq("normalized_name", company_name)
                .limit(1)
                .execute()
    )

    logger.info(f"company_id: {company_info} : company_name: {company_name}")
    if (company_info.data):
        company_id = company_info.data[0].get("id")
    
        db_ats_info = (
            supabase.table("company_ats")
                    .select("ats_id(name, ats_url), company_id(normalized_name)")
                    .eq("company_id", company_id)
                    .limit(1)
                    .execute()
        )
        logger.info(f"ats_info: {db_ats_info}")
        if (db_ats_info.data):
            ats_info = db_ats_info.data[0].get("ats_id")
        else:
            ats_info = fetch_new_company_ats(company_name)
    else:
        ats_info = fetch_new_company_ats(company_name)

    return (ats_info)
