# ============================================================================
# ATS URL patterns - used to recognize an ATS link once we already have a URL
# (e.g. from a careers page, or a search result).
# ============================================================================
ATS_PATTERNS = {
    "greenhouse": "greenhouse.io",
    "lever": "jobs.lever.co",
    "workday": "myworkdayjobs.com",
    "smartrecruiters": "smartrecruiters.com",
    "ashby": "jobs.ashbyhq.com",
}

# ============================================================================
# Tier-1 discovery: direct slug probing.
# Most ATS platforms expose a predictable public JSON/HTML endpoint keyed off
# a company "slug". If we can guess the slug, we can confirm the ATS with a
# single cheap HTTP call - no search engine involved at all.
#
# {slug} is substituted with each candidate slug generated from the company
# name (see core.search.careers_finder.generate_slug_candidates).
# ============================================================================
ATS_PROBE_ENDPOINTS = {
    "greenhouse": "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
    "lever": "https://jobs.lever.co/v0/postings/{slug}?mode=json",
    "smartrecruiters": "https://careers.smartrecruiters.com/{slug}/api/groups?page=1",
    "ashby": "https://api.ashbyhq.com/posting-api/job-board/{slug}",
}

# Human-facing board URL for each ATS, once a slug is confirmed valid.
ATS_BOARD_URL = {
    "greenhouse": "https://job-boards.greenhouse.io/{slug}",
    "lever": "https://jobs.lever.co/{slug}",
    "smartrecruiters": "https://careers.smartrecruiters.com/{slug}",
    "workday": "https://{slug}.wd1.myworkdayjobs.com",
    "ashby": "https://jobs.ashbyhq.com/{slug}",
}

# Platform-level URL templates stored in the `ats` registry.  Keep the
# company-specific part as a placeholder: a concrete board belongs in
# `company_ats.ats_url`, not in the shared ATS definition.
ATS_URL_TEMPLATES = {
    "greenhouse": "https://job-boards.greenhouse.io/{company}",
    "lever": "https://jobs.lever.co/{company}",
    "smartrecruiters": "https://careers.smartrecruiters.com/{company}",
    "workday": "https://{company}.wd1.myworkdayjobs.com",
    "ashby": "https://jobs.ashbyhq.com/{company}",
}

# Company legal-entity suffixes to strip before slugging ("Cato Networks Inc" -> "Cato Networks")
COMPANY_SUFFIXES = [
    "inc", "inc.", "llc", "llc.", "ltd", "ltd.", "corp", "corp.",
    "corporation", "co", "co.", "company", "group", "holdings",
    "technologies", "technology", "plc", "limited", "private", "pvt", "pvt."
]

CAREERS_KEYWORDS = {
    "careers",
    "jobs",
    "join",
    "work-with-us",
    "hiring",
    "work",
}

BAD_DOMAINS = {
    "linkedin.com",
    "indeed.com",
    "glassdoor.com",
    "youtube.com",
    "wikipedia.org",
    "crunchbase.com",
    "blogspot.com",
    "medium.com",
    "wordpress.com",
    "reddit.com",
    "bestbuyideas.com",
    "quora.com",
    "indeed.com",
    "jobstreet.com",
    "remoteok.com"
}
