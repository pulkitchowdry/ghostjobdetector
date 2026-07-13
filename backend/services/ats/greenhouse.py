import logging

import httpx

from .base import ATSAdapter, ATSJob

logger = logging.getLogger(__name__)


class GreenhouseAdapter(ATSAdapter):
    source_name = "greenhouse"

    async def list_jobs(self, ats_slug: str) -> list[ATSJob] | None:
        url = f"https://boards-api.greenhouse.io/v1/boards/{ats_slug}/jobs?content=true"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
        except Exception as e:
            logger.error(f"Greenhouse fetch failed for '{ats_slug}': {e}")
            return None

        if response.status_code != 200:
            logger.warning(f"Greenhouse returned {response.status_code} for '{ats_slug}'")
            return None

        raw_jobs = response.json().get("jobs", [])
        jobs: list[ATSJob] = []

        for job in raw_jobs:
            location = (job.get("location") or {}).get("name")
            departments = job.get("departments") or []
            department = departments[0]["name"] if departments else None

            jobs.append(
                ATSJob(
                    external_job_id=str(job.get("id")),
                    job_title=job.get("title", ""),
                    job_url=job.get("absolute_url"),
                    location=location,
                    department=department,
                    description=job.get("content"),
                    job_posted_at=job.get("first_published") or job.get("updated_at"),
                    job_updated_at=job.get("updated_at"),
                    raw_json=job,
                )
            )

        return jobs