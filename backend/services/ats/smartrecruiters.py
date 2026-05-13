import httpx
from .base import ATSAdapter, ATSResult
from utils.matchscoring import match_score
import logging
from bs4 import BeautifulSoup

# Need to implement pagination, find dateposted from the specific job posting details page
class SmartRecruitersAdapter(ATSAdapter):
    async def verify(self, company: str, job_title: str) -> ATSResult:
        url = f"https://careers.smartrecruiters.com/{company}/api/groups?page=1"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)

            if response.status_code != 200:
                return ATSResult(
                    exists=None,
                    confidence=0.0,
                    url=None,
                    source="smartrecruiters",
                    reason="Failed to fetch ATS page"
                )

            soup = BeautifulSoup(response.text, "html.parser")

            best_score = 0.0
            best_url = None
            best_title = None
            location_hint = None

            sections = soup.select("section.openings-section")

            for section in sections:
                location_el = section.select_one("h3.opening-title")
                location_hint = location_el.text.strip() if location_el else None

                jobs = section.select("li.opening-job")

                for job in jobs:
                    title_el = job.select_one("h4.job-title")
                    link_el = job.select_one("a")

                    if not title_el or not link_el:
                        continue

                    title = title_el.text.strip()
                    href = link_el.get("href")

                    score = match_score(title, job_title)

                    if score > best_score:
                        best_score = score
                        best_url = href
                        best_title = title

            # decision threshold (tune this later)
            exists = best_score >= 0.85

            return ATSResult(
                exists=exists,
                confidence=best_score,
                url=best_url,
                source="smartrecruiters",
                reason=f"Best match: {best_title} in {location_hint}"
            )

        except Exception as e:
            return ATSResult(
                exists=None,
                confidence=0.0,
                url=None,
                source="smartrecruiters",
                reason=f"Exception: {str(e)}"
            )
