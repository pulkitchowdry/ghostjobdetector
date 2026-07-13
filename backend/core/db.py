import os
from supabase import create_client, Client
import logging
from dotenv import load_dotenv

load_dotenv()
def init_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url:
        print("no url present")
    if not key:
        print("no key present")
    logger = logging.getLogger(__name__)

    logger.info(f"url: {url}")

    if not url or not key:
        raise ValueError("Missing Supabase config")

    return create_client(url, key)

supabase = init_supabase()
