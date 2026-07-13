import logging

import httpx

from .base import ATSAdapter, ATSJob

logger = logging.getLogger(__name__)


class AshbyAdapter(ATSAdapter):
    """Read public jobs from Ashby's unauthenticated job-board endpoint."""

    source_name = "ashby"

    async def list_jobs(self, ats_slug: str) -> list[ATSJob] | None:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{ats_slug}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
        except Exception as e:
            logger.error("Ashby fetch failed for '%s': %s", ats_slug, e)
            return None

        if response.status_code != 200:
            logger.warning("Ashby returned %s for '%s'", response.status_code, ats_slug)
            return None

        try:
            raw_jobs = response.json().get("jobs", [])
        except ValueError:
            logger.warning("Ashby returned invalid JSON for '%s'", ats_slug)
            return None

        jobs: list[ATSJob] = []
        for job in raw_jobs:
            if not job.get("isListed", True):
                continue

            job_url = job.get("jobUrl") or job.get("applyUrl")
            external_id = job.get("id") or job.get("jobPostingId") or job_url
            if not external_id or not job.get("title"):
                continue

            department = job.get("department") or job.get("team")
            jobs.append(
                ATSJob(
                    external_job_id=str(external_id),
                    job_title=job["title"],
                    job_url=job_url,
                    location=job.get("location"),
                    department=department,
                    employment_type=job.get("employmentType"),
                    description=job.get("descriptionHtml") or job.get("descriptionPlain"),
                    job_posted_at=job.get("publishedAt"),
                    job_updated_at=job.get("updatedAt"),
                    raw_json=job,
                )
            )

        return jobs
