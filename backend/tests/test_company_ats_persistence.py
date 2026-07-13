import unittest
from unittest.mock import patch

from data_services import ats_details, companies
from core.constants.ats_patterns import ATS_BOARD_URL, ATS_URL_TEMPLATES
from core.search.careers_finder import (
    _board_matches_company,
    _extract_ats_slug,
    _is_company_controlled_url,
    _looks_like_valid_board,
    generate_slug_candidates,
)
from services.ats.ashby import AshbyAdapter


class _Response:
    def __init__(self, data):
        self.data = data


class _AtsResponse:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


class _AsyncAtsResponse:
    status_code = 200

    def json(self):
        return {
            "jobs": [
                {
                    "id": "job-1",
                    "title": "Research Engineer",
                    "location": "San Francisco",
                    "department": "Research",
                    "jobUrl": "https://jobs.ashbyhq.com/openai/job-1",
                    "applyUrl": "https://jobs.ashbyhq.com/openai/job-1/application",
                    "isListed": True,
                },
                {"id": "hidden", "title": "Hidden", "isListed": False},
            ]
        }


class _AsyncClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None

    async def get(self, _url):
        return _AsyncAtsResponse()


class _Query:
    def __init__(self, table, result=None):
        self.table = table
        self.result = result

    def select(self, *_args):
        return self

    def eq(self, *_args):
        return self

    def limit(self, *_args):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def update(self, payload):
        self.table.operations.append(("update", payload))
        return self

    def insert(self, payload):
        self.table.operations.append(("insert", payload))
        return self

    def execute(self):
        return _Response(self.result or [])


class _Table:
    def __init__(self):
        self.operations = []

    def update(self, payload):
        self.operations.append(("update", payload))
        return _Query(self)

    def insert(self, payload):
        self.operations.append(("insert", payload))
        return _Query(self)


class _Supabase:
    def __init__(self):
        self.company_ats = _Table()

    def table(self, name):
        assert name == "company_ats"
        return self.company_ats


class CompanyAtsPersistenceTests(unittest.TestCase):
    def test_save_uses_insert_not_an_invalid_company_id_conflict_target(self):
        client = _Supabase()
        saved = {
            "id": "row-1",
            "company_id": "company-1",
            "ats_slug": "catonetworks",
            "ats_id": {"id": "ats-1", "name": "greenhouse"},
        }

        with patch.object(companies, "supabase", client), patch.object(
            companies,
            "get_company_ats_by_slug",
            side_effect=[None, saved],
        ):
            result = companies.upsert_company_ats(
                company_id="company-1",
                ats_id="ats-1",
                ats_slug="catonetworks",
                ats_url="https://boards.greenhouse.io/catonetworks",
                verified=True,
                sync_status="verified",
            )

        self.assertEqual(result, saved)
        self.assertEqual(client.company_ats.operations[0][0], "insert")
        self.assertEqual(
            client.company_ats.operations[0][1]["ats_slug"], "catonetworks"
        )

    def test_unverified_discovery_is_not_persisted(self):
        discovered = {
            "ats_name": "greenhouse",
            "ats_slug": None,
            "ats_url": "https://boards.greenhouse.io/example",
            "tier": 2,
        }
        with patch.object(
            ats_details, "get_or_create_company", return_value={"id": "company-1"}
        ), patch.object(ats_details, "get_company_ats", return_value=None), patch.object(
            ats_details, "discover_company_ats", return_value=discovered
        ), patch.object(ats_details, "upsert_company_ats") as save:
            result = ats_details.resolve_company_ats("Example")

        save.assert_not_called()
        self.assertFalse(result["verified"])
        self.assertIsNone(result["ats_slug"])

    def test_only_the_confirmed_slug_is_persisted(self):
        discovered = {
            "ats_name": "greenhouse",
            "ats_slug": "catonetworks",
            "ats_url": "https://boards.greenhouse.io/catonetworks",
            "verified": True,
            "tier": 1,
        }
        saved = {
            "ats_id": {"id": "ats-1", "name": "greenhouse"},
            "ats_slug": "catonetworks",
            "ats_url": discovered["ats_url"],
            "verified": True,
            "sync_status": "verified",
        }
        with patch.object(
            ats_details, "get_or_create_company", return_value={"id": "company-1"}
        ), patch.object(ats_details, "get_company_ats", return_value=None), patch.object(
            ats_details, "discover_company_ats", return_value=discovered
        ), patch.object(
            ats_details, "get_or_create_ats", return_value={"id": "ats-1"}
        ) as create_ats, patch.object(
            ats_details, "upsert_company_ats", return_value=saved
        ) as save:
            result = ats_details.resolve_company_ats("Cato Networks")

        self.assertTrue(result["verified"])
        self.assertEqual(result["ats_name"], "greenhouse")
        self.assertEqual(save.call_args.kwargs["ats_slug"], "catonetworks")
        self.assertEqual(
            create_ats.call_args.args[1],
            ATS_URL_TEMPLATES["greenhouse"],
        )

    def test_slug_generation_never_uses_only_the_first_word(self):
        self.assertEqual(
            generate_slug_candidates("Cato Networks, Inc."),
            ["catonetworks", "cato-networks"],
        )

    def test_existing_verified_board_is_not_replaced_by_a_new_guess(self):
        cached = {
            "ats_id": {"id": "ats-1", "name": "smartrecruiters"},
            "ats_slug": "freshworks",
            "ats_url": "https://careers.smartrecruiters.com/freshworks",
            "verified": True,
            "sync_status": "verified",
        }
        with patch.object(
            ats_details, "get_or_create_company", return_value={"id": "company-1"}
        ), patch.object(ats_details, "get_company_ats", return_value=cached), patch.object(
            ats_details, "discover_company_ats"
        ) as discover:
            result = ats_details.resolve_company_ats("Freshworks")

        discover.assert_not_called()
        self.assertEqual(result["ats_name"], "smartrecruiters")
        self.assertEqual(result["ats_slug"], "freshworks")

    def test_greenhouse_candidate_requires_company_name_match(self):
        response = _AtsResponse({"jobs": [{"company_name": "Anthropic"}]})
        self.assertTrue(_board_matches_company("greenhouse", response, "Anthropic"))
        self.assertFalse(_board_matches_company("greenhouse", response, "Meta"))
        self.assertEqual(
            ATS_BOARD_URL["greenhouse"].format(slug="anthropic"),
            "https://job-boards.greenhouse.io/anthropic",
        )

    def test_ashby_board_slug_and_company_domain_are_detected(self):
        self.assertEqual(
            _extract_ats_slug(
                "ashby", "https://jobs.ashbyhq.com/openai/job-id/application"
            ),
            "openai",
        )
        self.assertTrue(
            _is_company_controlled_url("https://openai.com/careers/search/", "OpenAI")
        )
        self.assertFalse(
            _is_company_controlled_url("https://example.com/careers/openai", "OpenAI")
        )

    def test_ats_probe_requires_a_non_empty_public_job_list(self):
        self.assertTrue(
            _looks_like_valid_board("ashby", _AtsResponse({"jobs": [{"title": "Role"}]}))
        )
        self.assertFalse(_looks_like_valid_board("ashby", _AtsResponse({"jobs": []})))


class AshbyAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_ashby_adapter_normalizes_public_listed_jobs(self):
        with patch("services.ats.ashby.httpx.AsyncClient", return_value=_AsyncClient()):
            jobs = await AshbyAdapter().list_jobs("openai")

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0].external_job_id, "job-1")
        self.assertEqual(jobs[0].job_title, "Research Engineer")


if __name__ == "__main__":
    unittest.main()
