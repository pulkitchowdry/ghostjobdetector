from core.db import supabase

def create_company(data: dict):
    res = supabase.table("companies")
            .insert(data)
            .execute()

    if res.error:
        raise Exception(res.error.message)

    return res.data[0] if res.data else None

def get_company_by_id(company_id: str):
    res = (
        supabase.table("companies")
        .select("*")
        .eq("id", company_id)
        .execute()
    )

    return res.data[0] if res.data else None

def get_company_by_name(name: str):
    res = (
        supabase.table("companies")
        .select("*")
        .eq("normalized_name", name.lower())
        .execute()
    )

    return res.data[0] if res.data else None

def update_company(company_id: str, data: dict):
    res = (
        supabase.table("companies")
        .update(data)
        .eq("id", company_id)
        .execute()
    )

    if res.error:
        raise Exception(res.error.message)

    return res.data

def upsert_company(data: dict):
    res = (
        supabase.table("companies")
        .upsert(data)
        .execute()
    )

    if res.error:
        raise Exception(res.error.message)

    return res.data

def delete_company(company_id: str):
    res = (
        supabase.table("companies")
        .delete()
        .eq("id", company_id)
        .execute()
    )

    return res.data

def create_company_ats_record(company_name: str, ats_name: str, ats_url: str):
    company_id = create_company(
        {
            name: company_name,
            normalized_name: company_name,
            
        }
    )
