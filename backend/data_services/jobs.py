"""
Data access for the `jobs` cache table and the `job_sync_log` audit table.

Goal: never call a live ATS more than once per company per TTL window
(default 7 days), regardless of how many users ask about that company's
jobs in between. Everything in between is served from Supabase.
"""

import logging
from datetime import datetime, timezone

from core.db import supabase
from services.ats.registry import ATS_REGISTRY
from services.ats.base import ATSJob

logger = logging.getLogger(__name__)

JOB_SYNC_TTL_DAYS = 7


def upsert_job(job: dict) -> dict | None:
    res = (
        supabase.table("jobs")
        .upsert(job, on_conflict="company_id,external_job_id")
        .execute()
    )
    return res.data[0] if res.data else None


def get_active_jobs(company_id: str) -> list[dict]:
    res = (
        supabase.table("jobs")
        .select("*")
        .eq("company_id", company_id)
        .eq("is_active", True)
        .execute()
    )
    return res.data or []


def get_jobs_by_company_ids(company_ids: list[str]) -> list[dict]:
    res = supabase.table("jobs").select("*").in_("company_id", company_ids).execute()
    return res.data or []


def mark_jobs_inactive(company_id: str, seen_external_ids: set[str]) -> None:
    """Any job we previously stored for this company that did NOT appear in
    the latest sync is treated as taken down / filled, rather than deleted -
    keeps history for uniqueness/repost detection."""
    existing = get_active_jobs(company_id)
    stale_ids = [j["external_job_id"] for j in existing if j["external_job_id"] not in seen_external_ids]

    if not stale_ids:
        return

    supabase.table("jobs").update({"is_active": False}).eq("company_id", company_id).in_(
        "external_job_id", stale_ids
    ).execute()


# ----------------------------------------------------------------------------
# job_sync_log
# ----------------------------------------------------------------------------
def get_latest_sync_log(company_id: str) -> dict | None:
    res = (
        supabase.table("job_sync_log")
        .select("*")
        .eq("company_id", company_id)
        .order("synced_at", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def log_sync(company_id: str, status: str, jobs_fetched: int, error_message: str | None = None) -> None:
    supabase.table("job_sync_log").insert(
        {
            "company_id": company_id,
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "jobs_fetched": jobs_fetched,
            "status": status,
            "error_message": error_message,
        }
    ).execute()


def _is_job_sync_stale(company_id: str) -> bool:
    latest = get_latest_sync_log(company_id)
    if not latest:
        return True

    synced_at = latest.get("synced_at")
    if not synced_at:
        return True

    try:
        synced_dt = datetime.fromisoformat(synced_at.replace("Z", "+00:00"))
    except ValueError:
        return True

    age = datetime.now(timezone.utc) - synced_dt
    return age.days >= JOB_SYNC_TTL_DAYS


def _to_row(job: ATSJob, company_id: str) -> dict:
    return {
        "company_id": company_id,
        "external_job_id": job.external_job_id,
        "job_title": job.job_title,
        "location": job.location,
        "department": job.department,
        "employment_type": job.employment_type,
        "job_url": job.job_url,
        "description": job.description,
        "job_posted_at": job.job_posted_at,
        "job_updated_at": job.job_updated_at,
        "job_application_deadline": job.job_application_deadline,
        "is_active": True,
        "raw_json": job.raw_json,
    }


async def get_or_sync_company_jobs(company_id: str, ats_name: str | None, ats_slug: str | None) -> list[dict]:
    """
    Returns this company's job postings, refreshing from the live ATS only
    if the cache is missing or older than JOB_SYNC_TTL_DAYS. This is the
    only function that should ever trigger a live ATS call for job listings
    - everything else should read from Supabase via get_active_jobs().
    """
    if not _is_job_sync_stale(company_id):
        logger.info(f"job cache fresh for company_id={company_id}, serving from Supabase")
        return get_active_jobs(company_id)

    if not ats_name or not ats_slug:
        # We don't have a confirmed ATS to sync from - just serve whatever
        # (possibly stale, possibly empty) cache we have.
        logger.info(f"no ATS/slug to sync for company_id={company_id}, serving cached/empty jobs")
        return get_active_jobs(company_id)

    adapter = ATS_REGISTRY.get(ats_name)
    if not adapter:
        logger.warning(f"no adapter registered for ats_name={ats_name}")
        return get_active_jobs(company_id)

    logger.info(f"job cache stale/missing for company_id={company_id} - syncing from {ats_name}:{ats_slug}")

    try:
        jobs = await adapter.list_jobs(ats_slug)
    except Exception as e:
        logger.error(f"list_jobs failed for {ats_name}:{ats_slug}: {e}")
        log_sync(company_id, status="error", jobs_fetched=0, error_message=str(e))
        return get_active_jobs(company_id)

    if jobs is None:
        log_sync(company_id, status="error", jobs_fetched=0, error_message="ATS returned no data")
        return get_active_jobs(company_id)

    seen_ids = set()
    for job in jobs:
        upsert_job(_to_row(job, company_id))
        seen_ids.add(job.external_job_id)

    mark_jobs_inactive(company_id, seen_ids)
    log_sync(company_id, status="success", jobs_fetched=len(jobs))

    return get_active_jobs(company_id)