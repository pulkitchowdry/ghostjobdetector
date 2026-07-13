"""
Company -> ATS resolution, with Supabase-backed caching.

This is the piece that answers: "do we already know how to verify jobs at
this company, and if not, can we find out - without hammering search/HTTP
on every single request?"

Flow:
  1. Look up (or create) the company row.
  2. Look up its cached company_ats row.
  3. If a verified board is cached -> return it as-is.
  4. Otherwise run the tiered discovery pipeline (core.search.careers_finder)
     and persist only an ATS slug that the ATS has confirmed.
"""

import logging

from core.constants.ats_patterns import ATS_URL_TEMPLATES
from core.search.careers_finder import discover_company_ats
from data_services.companies import (
    get_or_create_company,
    get_company_ats,
    get_or_create_ats,
    upsert_company_ats,
)

logger = logging.getLogger(__name__)

def _record_to_result(record: dict, company_id: str, source: str) -> dict:
    ats_info = record.get("ats_id") or {}
    # supabase embeds the joined row under the FK column name; ats_info may
    # be a dict (joined) or already resolved.
    ats_name = ats_info.get("name") if isinstance(ats_info, dict) else None

    return {
        "company_id": company_id,
        "ats_name": ats_name if ats_name != "unknown" else None,
        "ats_slug": record.get("ats_slug"),
        "ats_url": record.get("ats_url"),
        "verified": record.get("verified", False),
        "sync_status": record.get("sync_status"),
        "last_synced_at": record.get("last_synced_at"),
        "source": source,
    }


def resolve_company_ats(company_name: str) -> dict:
    company = get_or_create_company(company_name)
    company_id = company["id"]

    cached = get_company_ats(company_id)
    if cached:
        logger.info(f"using persisted verified ATS for '{company_name}' (status={cached.get('sync_status')})")
        return _record_to_result(cached, company_id, source="cache")

    logger.info(f"company_ats cache miss/stale for '{company_name}' - running discovery")
    discovered = discover_company_ats(company_name)

    # A board is persisted only after an ATS API check and confirmation that
    # it was linked from the company's own careers page.
    if (
        discovered
        and discovered.get("verified") is True
        and discovered.get("ats_name")
        and discovered.get("ats_slug")
    ):
        logger.info(f"Discoverved company ATS: ats_name: {discovered.get('ats_name')}; ats_slug: {discovered.get('ats_slug')}")
        ats_row = get_or_create_ats(
            discovered["ats_name"],
            ATS_URL_TEMPLATES[discovered["ats_name"]],
        )
        record = upsert_company_ats(
            company_id=company_id,
            ats_id=ats_row["id"],
            ats_slug=discovered.get("ats_slug"),
            ats_url=discovered.get("ats_url"),
            verified=True,
            sync_status="verified",
        )
        return _record_to_result(record, company_id, source=f"tier{discovered.get('tier')}")

    # The database schema requires ats_slug, so negative and partial results
    # are returned to the caller but never inserted into company_ats.
    if discovered:
        logger.info(f"sync_status: unverified")
        return {
            "company_id": company_id,
            "ats_name": discovered.get("ats_name"),
            "ats_slug": None,
            "ats_url": discovered.get("ats_url") or discovered.get("careers_url"),
            "verified": False,
            "sync_status": "unverified",
            "last_synced_at": None,
            "source": f"tier{discovered.get('tier')}",
        }

    logger.info(f"sync_status: not_found")
    return {
        "company_id": company_id,
        "ats_name": None,
        "ats_slug": None,
        "ats_url": None,
        "verified": False,
        "sync_status": "not_found",
        "last_synced_at": None,
        "source": "not_found",
    }
