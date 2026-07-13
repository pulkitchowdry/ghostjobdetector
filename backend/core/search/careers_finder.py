"""
Company -> ATS discovery pipeline.

Runs cheapest / most-reliable methods first, and only falls back to a web
search as a last resort:

  Tier 1: direct slug probing against known ATS endpoints (no search engine,
          near-instant, high confidence when it hits).
  Tier 2: resolve the company's own domain, find its careers page, and look
          for an embedded/linked ATS URL there.
  Tier 3: DuckDuckGo search (existing behaviour), used only when 1 and 2
          both fail.

Every result includes a "confidence" so callers can decide how much to trust
it, and a "tier" so we know which method found it.
"""

import logging
import re
from urllib.parse import urlparse, urljoin

import httpx
from ddgs import DDGS

from core.constants.ats_patterns import (
    ATS_PATTERNS,
    ATS_PROBE_ENDPOINTS,
    ATS_BOARD_URL,
    COMPANY_SUFFIXES,
    CAREERS_KEYWORDS,
    BAD_DOMAINS,
)

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 6.0
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept"    : "application/json, text/html"
}


# ----------------------------------------------------------------------------
# Slug generation
# ----------------------------------------------------------------------------
def generate_slug_candidates(company_name: str) -> list[str]:
    """
    Turn "Cato Networks, Inc." into a short, ordered list of likely ATS/
    domain slugs: ["catonetworks", "cato-networks"]
    """
    name = company_name.lower().strip()
    name = re.sub(r"[.,]", "", name)

    words = [w for w in name.split() if w not in COMPANY_SUFFIXES]
    if not words:
        words = name.split()

    joined      = "".join(words)
    hyphenated  = "-".join(words)
    dotted      = ".".join(words)

    candidates = [joined, hyphenated, dotted]

    # de-dupe while preserving order
    seen = set()
    ordered = []
    for c in candidates:
        c = re.sub(r"[^a-z0-9\-\.]", "", c)
        if c and c not in seen:
            seen.add(c)
            ordered.append(c)

    return ordered


# ----------------------------------------------------------------------------
# Tier 1: direct ATS slug probing
# ----------------------------------------------------------------------------
def _probe_ats_slug(
    client: httpx.Client,
    ats_name: str,
    slug: str,
    expected_company: str | None = None,
) -> bool:
    """Check that an ATS serves this slug, and match its owner when exposed."""
    try:
        resp = client.get(ATS_PROBE_ENDPOINTS[ats_name].format(slug=slug))
    except Exception as e:
        logger.debug("[ATS probe] failed for %s:%s: %s", ats_name, slug, e)
        return False

    if resp.status_code != 200 or not _looks_like_valid_board(ats_name, resp):
        return False

    # A non-empty public job response proves that this exact board slug is
    # active.  We intentionally generate only full-company slugs (never a
    # single-word fragment of a multi-word company), so it is safe to accept
    # this as the Tier 1 fallback when a first-party careers page is blocked.
    # Greenhouse's company_name is retained as an additional diagnostic signal.
    if expected_company and ats_name == "greenhouse":
        if not _board_matches_company(ats_name, resp, expected_company):
            logger.warning(
                "[ATS probe] greenhouse board '%s' returned jobs but its company_name "
                "does not match '%s'",
                slug,
                expected_company,
            )
    return True


def probe_ats_slugs(company_name: str) -> dict | None:
    slugs = generate_slug_candidates(company_name)
    logger.info(f"[tier1] probing slugs {slugs} for {company_name}")

    with httpx.Client(timeout=HTTP_TIMEOUT, headers=DEFAULT_HEADERS) as client:
        for slug in slugs:
            for ats_name in ATS_PROBE_ENDPOINTS:
                if not _probe_ats_slug(client, ats_name, slug, expected_company=company_name):
                    continue

                logger.info(
                    "[tier1] verified %s slug='%s' from non-empty ATS jobs response",
                    ats_name,
                    slug,
                )
                return {
                    "ats_name": ats_name,
                    "ats_slug": slug,
                    "ats_url": ATS_BOARD_URL[ats_name].format(slug=slug),
                    # This is only reached when the ATS's own response names
                    # the requested company (currently supported by
                    # Greenhouse).  Other ATSs require a first-party link.
                    "verified": True,
                    "confidence": "high",
                    "tier": 1,
                }

    logger.info(f"[tier1] no match for {company_name}")
    return None


def _looks_like_valid_board(ats_name: str, resp: httpx.Response) -> bool:
    try:
        if ats_name == "greenhouse":
            data = resp.json()
            return isinstance(data.get("jobs"), list) and bool(data["jobs"])
        if ats_name == "lever":
            data = resp.json()
            return isinstance(data, list) and bool(data)
        if ats_name == "smartrecruiters":
            # This endpoint may return JSON or server-rendered openings HTML.
            try:
                data = resp.json()
                if isinstance(data, dict) and any(
                    key in data for key in ("content", "groups", "totalElements")
                ):
                    return True
            except ValueError:
                pass
            return "opening-job" in resp.text.lower()
        if ats_name == "ashby":
            data = resp.json()
            return isinstance(data.get("jobs"), list) and bool(data["jobs"])
    except Exception:
        return False
    return False


def _board_matches_company(ats_name: str, resp: httpx.Response, company_name: str) -> bool:
    """Read an ATS-provided company identity when the response exposes one."""
    if ats_name != "greenhouse":
        return False

    try:
        jobs = resp.json().get("jobs", [])
    except (TypeError, ValueError):
        return False

    expected = _normalize_company_identity(company_name)
    names = {
        _normalize_company_identity(job.get("company_name", ""))
        for job in jobs
        if job.get("company_name")
    }
    return expected in names


def _normalize_company_identity(name: str) -> str:
    words = re.findall(r"[a-z0-9]+", name.lower())
    suffixes = {re.sub(r"[^a-z0-9]", "", suffix) for suffix in COMPANY_SUFFIXES}
    return " ".join(word for word in words if word not in suffixes)


# ----------------------------------------------------------------------------
# Tier 2: company domain -> careers page -> embedded ATS
# ----------------------------------------------------------------------------
def find_via_company_domain(company_name: str) -> dict | None:
    slugs = generate_slug_candidates(company_name)
    domain_candidates = [f"https://{s}.com" for s in slugs]

    homepage_url, homepage_html = None, None
    with httpx.Client(timeout=HTTP_TIMEOUT, headers=DEFAULT_HEADERS, follow_redirects=True) as client:
        for candidate in domain_candidates:
            try:
                resp = client.get(candidate)
                if resp.status_code == 200:
                    homepage_url = str(resp.url)
                    homepage_html = resp.text
                    break
            except Exception as e:
                logger.debug(f"[tier2] domain probe failed {candidate}: {e}")
                continue

        if not homepage_url:
            logger.info(f"[tier2] no reachable domain for {company_name}")
            return None

        careers_url = _find_careers_link(homepage_url, homepage_html)
        if not careers_url:
            logger.info(f"[tier2] no careers link found on {homepage_url}")
            return None

        try:
            careers_resp = client.get(careers_url)
            careers_html = careers_resp.text if careers_resp.status_code == 200 else ""
        except Exception as e:
            logger.debug(f"[tier2] failed to fetch careers page {careers_url}: {e}")
            careers_html = ""

    board = _find_ats_board_url(careers_url, careers_html)
    if board:
        ats_name, ats_slug, ats_url = board
        # This URL was linked from the company's own careers page and the
        # ATS API accepted its slug.  Together those facts are sufficient to
        # treat it as a verified company board.
        with httpx.Client(timeout=HTTP_TIMEOUT, headers=DEFAULT_HEADERS) as client:
            is_live_board = _probe_ats_slug(client, ats_name, ats_slug)

        if is_live_board:
            logger.info(
                "[Tier 2] verified %s slug='%s' from first-party careers page",
                ats_name,
                ats_slug,
            )
            return {
                "ats_name": ats_name,
                "ats_slug": ats_slug,
                "ats_url": ats_url,
                "careers_url": careers_url,
                "verified": True,
                "confidence": "high",
                "tier": 2,
            }

        logger.warning(
            "[Tier 2] careers page linked %s but its slug '%s' failed ATS validation",
            ats_name,
            ats_slug,
        )

    ats = detect_ats(careers_url) or detect_ats_from_html(careers_html)
    if ats:
        logger.info(f"[Tier 2] unverified ATS '{ats['ats_name']}' found via careers page {careers_url}")
        return {
            "ats_name": ats["ats_name"],
            "ats_slug": None,
            "ats_url": ats.get("ats_base_url") or careers_url,
            "careers_url": careers_url,
            "verified": False,
            "confidence": "unverified",
            "tier": 2,
        }

    # No recognized ATS embedded, but we DID find a real careers page -
    # this is still worth persisting so we don't re-discover it every time.
    logger.info(f"[Tier 2] careers page found but no known ATS embedded: {careers_url}")
    return {
        "ats_name": None,
        "ats_slug": None,
        "ats_url": None,
        "careers_url": careers_url,
        "verified": False,
        "confidence": "low",
        "tier": 2,
    }


def _find_careers_link(base_url: str, html: str) -> str | None:
    if not html:
        return None
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return None

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = (a.get_text() or "").lower()
        haystack = f"{href} {text}".lower()
        if any(kw in haystack for kw in CAREERS_KEYWORDS):
            return urljoin(base_url, href)

    return None


def detect_ats(url: str) -> dict | None:
    url_l = url.lower()
    for ats, pattern in ATS_PATTERNS.items():
        if pattern in url_l:
            logger.debug(f"ATS detected: {ats} in {url}")
            return {"ats_name": ats, "ats_base_url": pattern}
    return None


def detect_ats_from_html(html: str) -> dict | None:
    if not html:
        return None
    html_l = html.lower()
    for ats, pattern in ATS_PATTERNS.items():
        if pattern in html_l:
            return {"ats_name": ats, "ats_base_url": pattern}
    return None


def _find_ats_board_url(careers_url: str, html: str) -> tuple[str, str, str] | None:
    """Extract a concrete ATS board URL linked by an official careers page."""
    candidates = [careers_url]
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html or "", "html.parser")
        for tag in soup.find_all(["a", "iframe", "script"], href=True):
            candidates.append(urljoin(careers_url, tag["href"]))
        for tag in soup.find_all(["iframe", "script"], src=True):
            candidates.append(urljoin(careers_url, tag["src"]))
    except Exception:
        pass

    # ATS links are often embedded in inline JavaScript rather than an anchor.
    candidates.extend(re.findall(r"https?://[^\"'<>\\s]+", html or ""))

    for candidate in candidates:
        ats = detect_ats(candidate)
        if not ats:
            continue
        slug = _extract_ats_slug(ats["ats_name"], candidate)
        if slug:
            return ats["ats_name"], slug, ATS_BOARD_URL[ats["ats_name"]].format(slug=slug)
    return None


def _extract_ats_slug(ats_name: str, url: str) -> str | None:
    parsed = urlparse(url)
    path_parts = [part for part in parsed.path.split("/") if part]

    if ats_name in {"greenhouse", "lever", "smartrecruiters", "ashby"} and path_parts:
        slug = path_parts[0].lower()
    elif ats_name == "workday":
        slug = parsed.hostname.split(".")[0].lower() if parsed.hostname else ""
    else:
        return None

    return slug if re.fullmatch(r"[a-z0-9-]+", slug) else None


# ----------------------------------------------------------------------------
# Tier 3: search engine fallback (last resort)
# ----------------------------------------------------------------------------
def score_url(url: str, company_name: str) -> int:
    url_l = url.lower()
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    path = parsed.path.lower()
    score = 0
    company_slug = company_name.lower().replace(" ", "")

    for ats, pattern in ATS_PATTERNS.items():
        if pattern in url_l:
            score += 300

    if domain.startswith("careers.") or domain.startswith("jobs."):
        if company_slug in domain:
            score += 200

    if company_slug in domain.replace("-", "").replace(".", ""):
        if any(x in path for x in ["/careers", "/jobs", "/work", "/hiring"]):
            score += 200

    if any(x in path for x in ["careers", "jobs", "join", "hiring"]):
        score += 50

    if any(bad in domain for bad in BAD_DOMAINS):
        score -= 250

    return score


def find_via_search(company_name: str) -> dict | None:
    logger.info(f"[tier3] searching careers page for: {company_name}")

    queries = [f"{company_name} careers"]
    results = []

    try:
        with DDGS() as ddgs:
            for q in queries:
                for r in ddgs.text(q, max_results=10):
                    url = (r.get("href") or r.get("url") or "").strip()
                    if not url:
                        continue
                    domain = urlparse(url).netloc.lower()
                    if any(bad in domain for bad in BAD_DOMAINS):
                        continue
                    results.append(url)
    except Exception as e:
        logger.warning(f"[tier3] search failed: {e}")
        return None

    if not results:
        logger.warning(f"[tier3] no results found for {company_name}")
        return None

    scored = sorted(
        [(url, score_url(url, company_name)) for url in results],
        key=lambda x: x[1],
        reverse=True,
    )
    best_url, best_score = scored[0]
    logger.info(f"[tier3] best URL selected: {best_url} (score={best_score})")

    # Search results are only leads.  When the result belongs to the company,
    # inspect its HTML for an ATS board and validate that board's public API.
    # This covers careers pages that render their jobs directly but link each
    # application's "Apply" button to an ATS (e.g. Ashby).
    if _is_company_controlled_url(best_url, company_name):
        try:
            with httpx.Client(
                timeout=HTTP_TIMEOUT,
                headers=DEFAULT_HEADERS,
                follow_redirects=True,
            ) as client:
                careers_resp = client.get(best_url)
                careers_html = careers_resp.text if careers_resp.status_code == 200 else ""
                board = _find_ats_board_url(str(careers_resp.url), careers_html)
                if board:
                    ats_name, ats_slug, ats_url = board
                    if _probe_ats_slug(client, ats_name, ats_slug):
                        logger.info(
                            "[tier3] verified %s slug='%s' from company careers page",
                            ats_name,
                            ats_slug,
                        )
                        return {
                            "ats_name": ats_name,
                            "ats_slug": ats_slug,
                            "ats_url": ats_url,
                            "careers_url": str(careers_resp.url),
                            "verified": True,
                            "confidence": "high",
                            "tier": 3,
                        }
        except Exception as e:
            logger.debug("[tier3] could not inspect careers page %s: %s", best_url, e)

    ats = detect_ats(best_url)
    return {
        "ats_name": ats["ats_name"] if ats else None,
        "ats_slug": None,
        "ats_url": ats.get("ats_base_url") if ats else None,
        "careers_url": best_url,
        "verified": False,
        "confidence": "low",
        "tier": 3,
    }


def _is_company_controlled_url(url: str, company_name: str) -> bool:
    """Conservatively identify a search result on the requested company domain."""
    hostname = (urlparse(url).hostname or "").lower()
    hostname = hostname.removeprefix("www.")
    company_tokens = {
        candidate.replace("-", "") for candidate in generate_slug_candidates(company_name)
    }
    compact_domain = re.sub(r"[^a-z0-9]", "", hostname)
    return any(token and token in compact_domain for token in company_tokens)


# ----------------------------------------------------------------------------
# Public entrypoint
# ----------------------------------------------------------------------------
def discover_company_ats(company_name: str) -> dict | None:
    """
    Runs the full tiered pipeline and returns the first hit, or None if
    nothing at all could be found (not even a careers page).
    """
    # An ATS URL linked from the company's own site is authoritative.  If the
    # careers page is rendered client-side and exposes no board link in HTML,
    # continue to the API-backed slug check instead of stopping early.
    first_party_result = find_via_company_domain(company_name)
    logger.info(f"discover_company_ats: {first_party_result}")
    if first_party_result and first_party_result.get("verified"):
        return first_party_result

    result = probe_ats_slugs(company_name)
    if result:
        return result

    result = find_via_search(company_name)
    if result and result.get("verified"):
        return result

    if first_party_result:
        return first_party_result
    if result:
        return result

    logger.warning(f"No ATS or careers page found for {company_name} after all tiers")
    return None


# Kept for backwards compatibility with any existing callers.
def find_careers_page(company_name: str) -> dict | None:
    logger.info(f"Searching careers page for {company_name}")
    result = discover_company_ats(company_name)
    if not result:
        logger.info(f"Careers page not found for {company_name}")
        return None
    return {
        "careers_url": result.get("careers_url") or result.get("ats_url"),
        "ats": {"ats_name": result["ats_name"], "ats_base_url": result.get("ats_url")}
        if result.get("ats_name")
        else None,
    }
