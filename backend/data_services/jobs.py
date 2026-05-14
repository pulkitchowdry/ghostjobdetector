from core.db import supabase
from .companies import get_company_by_id, get_company_ats

def upsert_job(job: dict):
    res = (
        supabase.table("jobs")
        .upsert(job, on_conflict="company_id,external_job_id")
        .execute()
    )

    return res.data

def get_active_jobs(company_id: str):
    res = (
        supabase.table("jobs")
        .select("*")
        .eq("company_id", company_id)
        .eq("is_active", True)
        .execute()
    )

    return res.data

def get_jobs_by_company_ids(company_ids: list[str]):
    res = (
        supabase.table("jobs")
        .select("*")
        .in_("company_id", company_ids)
        .execute()
    )

    return res.data

def sync_company_jobs(company_id: str):
    company = get_company_by_id(company_id)

    ats = get_company_ats(company_id)

    jobs = fetch_from_ats(ats)

    for job in jobs:
        upsert_job(job)
