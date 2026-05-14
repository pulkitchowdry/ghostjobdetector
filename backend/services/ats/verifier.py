from .registry import ATS_REGISTRY
import logging
from .base import ATSResult

async def verify_ats(company_name: str, job_title: str, ats_type: str, ats_company: str) -> ATSResult:
    logger = logging.getLogger("verify_ats")
    company_lower = company_name.lower().strip()

    cache_key = f"{company_lower}:{job_title.lower()[:60]}:{ats_type}"

    # logger.info(f"cache_key: {cache_key}")
    # logger.info(f"ats_cache: {ats_cache}")
    # if cache_key in ats_cache:
    #     return ats_cache[cache_key]

    adapter = ATS_REGISTRY.get(ats_type)

    logger.info(f"adapter: {adapter}")
    if not adapter:
        result = ATSResult(
            exists=None,
            confidence=0.0,
            url=None,
            source=ats_type,
            reason="No adapter available",
            created_at=None,
            updated_at=None,
            application_deadline=None,
        )
        return result

    result = await adapter.verify(ats_company, job_title)

    # ats_cache[cache_key] = result

    return result
