import httpx
from .base import ATSAdapter, ATSResult
from utils.matchscoring import match_score
import logging

## Need to implement proper parsing
class GreenhouseAdapter(ATSAdapter):
    async def verify(self, company: str, job_title: str) -> ATSResult:
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)

        if response.status_code != 200:
            return ATSResult(None, 0.0, None, "greenhouse", "API failed")

        jobs = response.json().get("jobs", [])

        best_score = 0.0
        best_url = None
        best_title = None

        for job in jobs:
            score = match_score(job.get("title", ""), job_title)
            created_at = job.get("first_published")
            updated_at = job.get("updated_at")
            application_deadline = job.get("application_deadline")

            if score > best_score:
                best_score = score
                best_title = job.get("title")
                best_url = job.get("absolute_url")

        return ATSResult(
            exists=best_score >= 0.85,
            confidence=best_score,
            url=best_url,
            source="greenhouse",
            reason=f"Best match: {best_title}",
            created_at=created_at,
            updated_at=updated_at,
            application_deadline=application_deadline
        )