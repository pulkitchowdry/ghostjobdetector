# ============================================================================
# Lightweight role-category taxonomy.
#
# Purpose: catch the case where a job's TITLE says one role ("Software
# Engineer") but its DESCRIPTION content is actually about something else
# entirely ("...5 years experience in a fast-paced kitchen, food safety
# certification required..."). Pure keyword regex on the description alone
# can't see this, because it only ever looks at the description in
# isolation - it needs to be checked against the title.
#
# This is intentionally NOT an ML/embedding model: it's a small, explainable,
# dependency-free dictionary that's cheap to run on every request (including
# on Lambda) and easy for a non-ML engineer to extend. It's a starting point;
# a sentence-embedding model (e.g. all-MiniLM-L6-v2) is a natural upgrade
# path later if/when the taxonomy's false-negative rate becomes a problem -
# see the note at the bottom of this file.
# ============================================================================

ROLE_CATEGORIES: dict[str, dict[str, list[str]]] = {
    "software_engineering": {
        "title_keywords": [
            "software engineer", "developer", "programmer", "backend",
            "front end", "frontend", "full stack", "fullstack", "devops",
            "site reliability", "sre", "data engineer", "ml engineer",
            "machine learning engineer", "mobile engineer", "qa engineer",
            "sdet", "platform engineer", "infrastructure engineer",
        ],
        "content_keywords": [
            "python", "java", "javascript", "typescript", "react", "node",
            "aws", "gcp", "azure", "kubernetes", "docker", "git", "api",
            "database", "sql", "microservices", "algorithm", "unit test",
            "ci/cd", "codebase", "repository", "agile", "sprint", "backend",
            "frontend", "rest api", "graphql", "cloud infrastructure",
        ],
    },
    "sales": {
        "title_keywords": [
            "sales", "account executive", "business development",
            "sdr", "bdr", "account manager", "sales representative",
        ],
        "content_keywords": [
            "quota", "pipeline", "crm", "salesforce", "prospecting",
            "closing deals", "revenue target", "cold call", "leads",
            "commission", "book of business", "outbound", "upsell",
        ],
    },
    "marketing": {
        "title_keywords": [
            "marketing", "growth marketing", "content marketing", "seo",
            "brand manager", "social media manager", "demand generation",
        ],
        "content_keywords": [
            "campaign", "engagement", "conversion rate", "analytics",
            "brand awareness", "content calendar", "ad spend", "seo",
            "email marketing", "audience segmentation", "ctr",
        ],
    },
    "food_hospitality": {
        "title_keywords": [
            "chef", "cook", "kitchen", "server", "waiter", "waitress",
            "barista", "bartender", "hospitality", "restaurant", "culinary",
            "sous chef", "line cook", "host", "hostess",
        ],
        "content_keywords": [
            "menu", "recipe", "food safety", "kitchen", "culinary", "dish",
            "ingredients", "cuisine", "food handler", "prep station",
            "dining", "shift meal", "servsafe", "food service",
        ],
    },
    "healthcare": {
        "title_keywords": [
            "nurse", "physician", "doctor", "medical assistant", "clinical",
            "therapist", "pharmacist", "caregiver", "rn", "lpn",
        ],
        "content_keywords": [
            "patient", "clinical", "diagnosis", "treatment", "medical record",
            "hipaa", "license", "hospital", "healthcare", "vitals",
            "bedside", "ehr",
        ],
    },
    "finance_accounting": {
        "title_keywords": [
            "accountant", "financial analyst", "controller", "bookkeeper",
            "auditor", "finance manager", "treasury",
        ],
        "content_keywords": [
            "gaap", "balance sheet", "reconciliation", "general ledger",
            "audit", "financial statements", "budgeting", "tax filing",
            "accounts payable", "accounts receivable", "p&l",
        ],
    },
    "design": {
        "title_keywords": [
            "designer", "ux designer", "ui designer", "product designer",
            "graphic designer", "visual designer",
        ],
        "content_keywords": [
            "figma", "wireframe", "prototype", "user research",
            "design system", "typography", "sketch app", "usability",
            "user flow", "mockup",
        ],
    },
    "customer_support": {
        "title_keywords": [
            "customer support", "customer success", "support specialist",
            "help desk", "technical support",
        ],
        "content_keywords": [
            "ticket", "zendesk", "customer satisfaction", "sla",
            "troubleshoot", "escalation", "csat", "live chat support",
        ],
    },
    "operations_admin": {
        "title_keywords": [
            "operations", "administrative assistant", "office manager",
            "executive assistant", "coordinator", "operations manager",
        ],
        "content_keywords": [
            "scheduling", "logistics", "vendor management",
            "office supplies", "calendar management", "travel arrangements",
            "process improvement",
        ],
    },
    "warehouse_logistics": {
        "title_keywords": [
            "warehouse", "logistics", "forklift", "delivery driver",
            "shipping", "receiving clerk",
        ],
        "content_keywords": [
            "inventory", "shipment", "forklift", "pallet", "loading dock",
            "supply chain", "warehouse management system", "packing",
        ],
    },
}


def _classify_title(title: str) -> str | None:
    title_l = title.lower()
    best_category, best_hits = None, 0

    for category, kws in ROLE_CATEGORIES.items():
        hits = sum(1 for kw in kws["title_keywords"] if kw in title_l)
        if hits > best_hits:
            best_hits = hits
            best_category = category

    return best_category


def _score_content_categories(description: str) -> dict[str, int]:
    desc_l = description.lower()
    return {
        category: sum(1 for kw in kws["content_keywords"] if kw in desc_l)
        for category, kws in ROLE_CATEGORIES.items()
    }


def compute_role_relevance(job_title: str, description: str) -> dict:
    """
    Returns:
        {
          "relevance_score": int 0-100,
          "confident": bool,          # whether this verdict should gate the overall score
          "reason": str,              # human-readable explanation for the UI/insights
          "title_category": str|None,
          "content_category": str|None,
        }
    """
    title_category = _classify_title(job_title)

    if not title_category:
        return {
            "relevance_score": 60,
            "confident": False,
            "reason": "Could not classify the job title into a known role category",
            "title_category": None,
            "content_category": None,
        }

    category_hits = _score_content_categories(description)
    total_hits = sum(category_hits.values())

    if total_hits == 0:
        return {
            "relevance_score": 50,
            "confident": False,
            "reason": "Description doesn't contain enough role-specific content to classify",
            "title_category": title_category,
            "content_category": None,
        }

    content_category, top_hits = max(category_hits.items(), key=lambda kv: kv[1])
    own_hits = category_hits.get(title_category, 0)

    # Strong, confident mismatch: description clearly matches a DIFFERENT
    # category and has zero signal for the title's own category.
    if own_hits == 0 and content_category != title_category and top_hits >= 2:
        return {
            "relevance_score": 10,
            "confident": True,
            "reason": (
                f"Title suggests '{title_category.replace('_', ' ')}' but the description "
                f"content matches '{content_category.replace('_', ' ')}'"
            ),
            "title_category": title_category,
            "content_category": content_category,
        }

    if content_category == title_category:
        return {
            "relevance_score": 90,
            "confident": True,
            "reason": f"Description content matches the stated role ({title_category.replace('_', ' ')})",
            "title_category": title_category,
            "content_category": content_category,
        }

    # Ambiguous / partial overlap - don't hard-gate, just nudge the score.
    ratio = own_hits / max(top_hits, 1)
    relevance_score = int(40 + ratio * 40)
    return {
        "relevance_score": relevance_score,
        "confident": False,
        "reason": f"Partial match to the stated role ({title_category.replace('_', ' ')})",
        "title_category": title_category,
        "content_category": content_category,
    }


# ----------------------------------------------------------------------------
# Future upgrade path (not implemented here to avoid a heavy Lambda
# dependency at this stage):
#
#   Replace _classify_title / _score_content_categories with cosine
#   similarity between a sentence-embedding of the description and a
#   canonical reference description per O*NET occupation code. Keep the
#   same compute_role_relevance() return shape so callers don't need to
#   change - only the internals would swap out.
# ----------------------------------------------------------------------------