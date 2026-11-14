import unittest

from scripts.update_jobs import (
    OntarioSearchFormParser,
    SOURCES,
    has_access_challenge,
    parse_ontario,
)


class OntarioJobsTests(unittest.TestCase):
    def test_search_form_preserves_state_and_submits_search_button(self):
        parser = OntarioSearchFormParser()
        parser.feed(
            '<form method="post" action="Search.aspx">'
            '<input type="hidden" name="__VIEWSTATE" value="state">'
            '<select name="city"><option value="">All cities</option>'
            '<option value="Toronto">Toronto</option></select>'
            '<input type="submit" name="searchButton" value="Search">'
            "</form>"
        )

        self.assertEqual(parser.form_attrs["method"], "post")
        self.assertEqual(
            dict(parser.post_data()),
            {"__VIEWSTATE": "state", "city": "", "searchButton": "Search"},
        )

    def test_parses_job_details_from_search_result_rows(self):
        source = next(source for source in SOURCES if source[0] == "ontario")
        html = (
            "<table><tr><th>Job title</th><th>Location</th></tr>"
            "<tr><td><a href='JobDetails.aspx?Language=English&amp;JobID=42'>"
            "Policy Analyst</a></td><td>Toronto</td>"
            "<td>December 1, 2026</td></tr></table>"
        )

        jobs = parse_ontario(source, html)

        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["title"], "Policy Analyst")
        self.assertEqual(jobs[0]["region"], "Ontario")
        self.assertEqual(jobs[0]["closingDate"], "")
        self.assertIn("JobID=42", jobs[0]["sourceUrl"])

    def test_keeps_all_results_beyond_other_sources_default_limit(self):
        source = next(source for source in SOURCES if source[0] == "ontario")
        rows = "".join(
            f"<tr><td><a href='JobDetails.aspx?JobID={job_id}'>"
            f"Public Service Role {job_id}</a></td><td>Toronto</td></tr>"
            for job_id in range(51)
        )

        jobs = parse_ontario(source, f"<table>{rows}</table>")

        self.assertEqual(len(jobs), 51)

    def test_detects_portal_access_challenge(self):
        self.assertTrue(has_access_challenge(
            "Radware CAPTCHA: please solve this CAPTCHA to request unblock"
        ))


if __name__ == "__main__":
    unittest.main()
