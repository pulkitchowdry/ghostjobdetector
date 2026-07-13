import logging

from .base import ATSResult
from utils.matchscoring import match_score
from data_services.ats_details import resolve_company_ats
from data_services.jobs import get_or_sync_company_jobs

logger = logging.getLogger("verify_ats")

MATCH_THRESHOLD = 0.85


async def verify_ats(company_name: str, job_title: str) -> ATSResult:
    """
    Resolve the company's ATS (from Supabase cache, or discover + persist it
    if unknown/stale), pull its cached job list (refreshed at most once a
    week), and match the given job title against it.

    No live ATS call happens on this request path unless the company's
    cached job list is missing or older than the sync TTL.
    """
    ats_record = resolve_company_ats(company_name)
    logger.info(f"resolved ats_record: {ats_record}")

    if not ats_record.get("verified"):
        return ATSResult(
            exists=None,
            confidence=0.0,
            url=ats_record.get("ats_url"),
            source=ats_record.get("ats_name") or "none",
            reason="No verified ATS slug is available for this company",
        )

    jobs = await get_or_sync_company_jobs(
        company_id=ats_record["company_id"],
        ats_name=ats_record.get("ats_name"),
        ats_slug=ats_record.get("ats_slug"),
    )

    if not jobs:
        return ATSResult(
            exists=False,
            confidence=0.0,
            url=None,
            source=ats_record.get("ats_name") or "unknown",
            reason="Company ATS verified, but no active postings found",
        )

    best_score = 0.0
    best_job = None
    for job in jobs:
        score = match_score(job.get("job_title") or "", job_title)
        if score > best_score:
            best_score = score
            best_job = job

    exists = best_score >= MATCH_THRESHOLD

    return ATSResult(
        exists=exists,
        confidence=best_score,
        url=best_job.get("job_url") if best_job else None,
        source=ats_record.get("ats_name") or "unknown",
        reason=(
            f"Matched against {len(jobs)} cached postings "
            f"(last synced {ats_record.get('last_synced_at')}). "
            f"Best match: {best_job.get('job_title') if best_job else 'none'}"
        ),
        created_at=best_job.get("job_posted_at") if best_job else None,
        updated_at=best_job.get("job_updated_at") if best_job else None,
        application_deadline=best_job.get("job_application_deadline") if best_job else None,
    )
