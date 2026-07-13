import logging

import httpx
from bs4 import BeautifulSoup

from .base import ATSAdapter, ATSJob

logger = logging.getLogger(__name__)


class SmartRecruitersAdapter(ATSAdapter):
    source_name = "smartrecruiters"

    async def list_jobs(self, ats_slug: str) -> list[ATSJob] | None:
        url = f"https://careers.smartrecruiters.com/{ats_slug}/api/groups?page=1"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
        except Exception as e:
            logger.error(f"SmartRecruiters fetch failed for '{ats_slug}': {e}")
            return None

        if response.status_code != 200:
            logger.warning(f"SmartRecruiters returned {response.status_code} for '{ats_slug}'")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        jobs: list[ATSJob] = []

        sections = soup.select("section.openings-section")
        for section in sections:
            location_el = section.select_one("h3.opening-title")
            location_hint = location_el.text.strip() if location_el else None

            for job_el in section.select("li.opening-job"):
                title_el = job_el.select_one("h4.job-title")
                link_el = job_el.select_one("a")

                if not title_el or not link_el:
                    continue

                title = title_el.text.strip()
                href = link_el.get("href")
                # href is typically a relative/partial path; SmartRecruiters
                # job IDs live in the URL, use it as the external id.
                external_id = href.rstrip("/").split("/")[-1] if href else title

                jobs.append(
                    ATSJob(
                        external_job_id=external_id,
                        job_title=title,
                        job_url=href,
                        location=location_hint,
                        raw_json={"title": title, "href": href, "location": location_hint},
                    )
                )

        # NOTE: pagination is not implemented yet - this only captures page 1.
        # Good enough for an early-stage cache; flagged as a follow-up.
        return jobs