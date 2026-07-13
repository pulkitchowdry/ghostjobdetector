"""
Data access for `companies`, `ats`, and `company_ats` tables.

`ats` is a small lookup/registry table (one row per ATS platform, e.g.
"greenhouse", "smartrecruiters", "unknown"). `company_ats` is the per-company
cache of which ATS (if any) was resolved for them, when it was last checked,
and whether it's still considered fresh - this is what lets us avoid
re-running discovery (slug probing / careers page scraping / search) on
every single request.
"""

import logging
import re
from datetime import datetime, timezone

from core.db import supabase

logger = logging.getLogger(__name__)


def normalize_company_name(name: str) -> str:
    normalized = name.lower().strip()
    normalized = re.sub(r"[^a-z0-9\s]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized


# ----------------------------------------------------------------------------
# companies
# ----------------------------------------------------------------------------
def get_company_by_id(company_id: str) -> dict | None:
    res = supabase.table("companies").select("*").eq("id", company_id).limit(1).execute()
    return res.data[0] if res.data else None


def get_company_by_name(name: str) -> dict | None:
    normalized = normalize_company_name(name)
    res = (
        supabase.table("companies")
        .select("*")
        .eq("normalized_name", normalized)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_or_create_company(name: str, domain: str | None = None) -> dict:
    existing = get_company_by_name(name)
    if existing:
        return existing

    normalized = normalize_company_name(name)
    payload = {
        "name": name.strip(),
        "normalized_name": normalized,
    }
    if domain:
        payload["domain"] = domain

    try:
        res = supabase.table("companies").insert(payload).execute()
        if res.data:
            logger.info(f"Created new company record for '{name}'")
            return res.data[0]
    except Exception as e:
        # Race condition guard: another request may have inserted the same
        # company between our lookup and insert (unique constraint on
        # normalized_name). Fall back to re-reading it.
        logger.warning(f"Insert failed for company '{name}', re-checking cache: {e}")

    existing = get_company_by_name(name)
    if existing:
        return existing

    raise RuntimeError(f"Could not create or find company record for '{name}'")


# ----------------------------------------------------------------------------
# ats (registry of platforms)
# ----------------------------------------------------------------------------
def get_ats_by_name(name: str) -> dict | None:
    res = supabase.table("ats").select("*").eq("name", name).limit(1).execute()
    return res.data[0] if res.data else None


def get_or_create_ats(name: str, ats_url: str | None = None) -> dict:
    existing = get_ats_by_name(name)
    if existing:
        return existing

    payload = {"name": name}
    if ats_url:
        payload["ats_url"] = ats_url

    try:
        res = supabase.table("ats").insert(payload).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        logger.warning(f"Insert failed for ats '{name}', re-checking: {e}")

    existing = get_ats_by_name(name)
    if existing:
        return existing

    raise RuntimeError(f"Could not create or find ats registry row for '{name}'")


# ----------------------------------------------------------------------------
# company_ats (per-company cache of the resolved ATS)
# ----------------------------------------------------------------------------
def get_company_ats(company_id: str) -> dict | None:
    """
    Returns the cached company_ats row (joined with the ats registry row),
    or None if we've never resolved this company before.
    """
    res = (
        supabase.table("company_ats")
        .select("*, ats_id(id, name, ats_url)")
        .eq("company_id", company_id)
        .eq("verified", True)
        .order("last_synced_at", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_company_ats_by_slug(company_id: str, ats_slug: str) -> dict | None:
    """Return the one cached, verified ATS board for this company and slug."""
    res = (
        supabase.table("company_ats")
        .select("*, ats_id(id, name, ats_url)")
        .eq("company_id", company_id)
        .eq("ats_slug", ats_slug)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def upsert_company_ats(
    company_id: str,
    ats_id: str | None,
    ats_slug: str | None,
    ats_url: str | None,
    verified: bool,
    sync_status: str,
) -> dict:
    """Store one *confirmed* ATS slug.

    ``company_ats.company_id`` is intentionally not unique in the deployed
    schema, so PostgREST cannot use it as an ``ON CONFLICT`` target.  Look up
    the exact company/slug row and update it by primary key instead.  This
    also prevents generated probe candidates from ever being stored.
    """
    if not ats_id:
        raise ValueError("A verified company_ats record requires an ats_id")
    if not ats_slug:
        raise ValueError("A verified company_ats record requires an ats_slug")

    now = datetime.now(timezone.utc).isoformat()

    payload = {
        "company_id": company_id,
        "ats_id": ats_id,
        "ats_slug": ats_slug,
        "ats_url": ats_url,
        "verified": verified,
        "sync_status": sync_status,
        "last_synced_at": now,
    }

    existing = get_company_ats_by_slug(company_id, ats_slug)
    if existing:
        supabase.table("company_ats").update(payload).eq("id", existing["id"]).execute()
    else:
        supabase.table("company_ats").insert(payload).execute()

    # Read through the relationship so callers consistently receive the ATS
    # name, including when PostgREST returns only the raw ``ats_id`` on write.
    saved = get_company_ats_by_slug(company_id, ats_slug)
    if saved:
        return saved

    raise RuntimeError(
        f"Failed to save company_ats for company_id={company_id}, ats_slug={ats_slug}"
    )
