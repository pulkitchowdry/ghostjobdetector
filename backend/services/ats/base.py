from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ATSResult:
    exists: Optional[bool]
    confidence: float
    url: Optional[str]
    source: str
    reason: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    application_deadline: Optional[datetime] = None


@dataclass
class ATSJob:
    """A single job posting as returned by an ATS adapter's list_jobs(),
    normalized to line up with the `jobs` table columns."""
    external_job_id: str
    job_title: str
    job_url: Optional[str] = None
    location: Optional[str] = None
    department: Optional[str] = None
    employment_type: Optional[str] = None
    description: Optional[str] = None
    job_posted_at: Optional[str] = None
    job_updated_at: Optional[str] = None
    job_application_deadline: Optional[str] = None
    raw_json: dict = field(default_factory=dict)


class ATSAdapter(ABC):
    @abstractmethod
    async def list_jobs(self, ats_slug: str) -> list[ATSJob]:
        """Fetch the full current job list for a company's board. This is
        the only method that should ever hit the live ATS - callers should
        cache the result (see data_services.jobs) rather than calling this
        per-request."""
        raise NotImplementedError

    async def verify(self, company: str, job_title: str) -> ATSResult:
        """Default implementation: list all jobs and pick the best title
        match. Adapters can override if they have a cheaper single-job
        lookup available."""
        from utils.matchscoring import match_score

        jobs = await self.list_jobs(company)
        if jobs is None:
            return ATSResult(None, 0.0, None, self.source_name, "Failed to fetch ATS listings")

        best_score = 0.0
        best_job: Optional[ATSJob] = None
        for job in jobs:
            score = match_score(job.job_title or "", job_title)
            if score > best_score:
                best_score = score
                best_job = job

        if not best_job:
            return ATSResult(False, 0.0, None, self.source_name, "No jobs found on ATS board")

        return ATSResult(
            exists=best_score >= 0.85,
            confidence=best_score,
            url=best_job.job_url,
            source=self.source_name,
            reason=f"Best match: {best_job.job_title}",
            created_at=best_job.job_posted_at,
            updated_at=best_job.job_updated_at,
            application_deadline=best_job.job_application_deadline,
        )

    @property
    def source_name(self) -> str:
        return self.__class__.__name__.replace("Adapter", "").lower()