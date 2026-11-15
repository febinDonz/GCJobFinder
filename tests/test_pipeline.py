"""Unit tests for the pure parts of the pipeline.

The Job Bank HTML below is a synthetic card shaped like the structure observed
on Job Bank result pages (title, date, employer, place, salary, job number).
It is NOT a captured page, so the first live run is the real check; the
sources table on the site reports what each source actually returned.
"""
import unittest

from scripts.govjobs import jobbank
from scripts.govjobs.common import make_job, parse_date
from scripts.govjobs.run import dedupe, merge

SOURCE = ("jb-ontario", "Ontario Public Service (via Job Bank)", "Provincial", "Ontario", "https://x", "jobbank")
GROUP = jobbank.GROUPS[0]

CARD = """
<article><a href="/jobsearch/jobposting/50497820;jsessionid=ABC?source=searchresults">
  <span>New</span><span>On site</span>
  <h3>Employment consultant <span>Save to favourites</span></h3>
  <ul><li>October 14, 2026</li><li>Ontario Public Service</li>
  <li>Toronto (ON)</li><li>$27.88 hourly</li><li>Job Bank #50497820</li></ul>
</a></article>
<article><a href="/jobsearch/jobposting/50497821">
  <h3>Policy analyst</h3><ul><li>October 15, 2026</li><li>Ontario Public Service</li>
  <li>Thunder Bay (ON)</li></ul></a></article>
"""


class ParseTests(unittest.TestCase):
    def test_parse_date(self):
        self.assertEqual(parse_date("October 14, 2026"), "2026-10-14")
        self.assertEqual(parse_date("Closes 2026-11-15 EST"), "2026-11-15")
        self.assertEqual(parse_date("soon"), "")

    def test_make_job_rejects_bad_url(self):
        self.assertIsNone(make_job(SOURCE, "Title", "Emp", "Loc", "javascript:alert(1)"))

    def test_jobbank_cards(self):
        jobs, ids = jobbank.parse_results(CARD, GROUP, "Ontario Public Service", SOURCE)
        self.assertEqual(ids, {"50497820", "50497821"})
        first = next(j for j in jobs if j["url"].endswith("50497820"))
        self.assertEqual(first["title"], "Employment consultant")
        self.assertEqual(first["posted"], "2026-10-14")
        self.assertEqual(first["employer"], "Ontario Public Service")
        self.assertEqual(first["location"], "Toronto (ON)")
        self.assertEqual(first["region"], "Ontario")
        self.assertIn("27.88", first["salary"])
        self.assertNotIn("jsessionid", first["url"])

    def test_source_labels_are_never_the_title(self):
        card = """<a href="/jobsearch/jobposting/50500001">
          <span>This job was posted directly by the employer on Job Bank.</span>
          <h3>Librarian</h3><ul><li>October 20, 2026</li><li>Ontario Public Service</li>
          <li>Maidstone (ON)</li></ul></a>
          <a href="/jobsearch/jobposting/50500002"><span>Jobs.gc.ca</span>
          <h3>Border services officer</h3><ul><li>October 20, 2026</li>
          <li>Canada Border Services Agency</li><li>Ottawa (ON)</li></ul></a>"""
        jobs, _ = jobbank.parse_results(card, GROUP, "Ontario Public Service", SOURCE)
        self.assertEqual(sorted(j["title"] for j in jobs), ["Border services officer", "Librarian"])

    def test_label_only_card_is_dropped(self):
        card = '<a href="/jobsearch/jobposting/50500003"><span>Jobs.gc.ca</span></a>'
        jobs, _ = jobbank.parse_results(card, GROUP, "Ontario Public Service", SOURCE)
        self.assertEqual(jobs, [])


class MergeTests(unittest.TestCase):
    def job(self, **over):
        base = {"id": "a", "title": "T", "employer": "E", "location": "L", "closing": "",
                "source": "bc", "direct": True, "posted": "2026-11-01"}
        return {**base, **over}

    def status(self, key, state):
        return {"key": key, "label": key, "government": "Provincial", "region": "X", "status": state, "count": 0}

    def test_expired_jobs_dropped(self):
        out = merge(None, [self.job(closing="2026-11-01")], [self.status("bc", "ok")], "2026-11-14", "t")
        self.assertEqual(out["jobs"], [])

    def test_failed_source_keeps_recent_jobs(self):
        prev = {"jobs": [self.job(firstSeen="2026-11-10", lastSeen="2026-11-13")],
                "sources": [{**self.status("bc", "ok"), "lastOk": "2026-11-13"}]}
        out = merge(prev, [], [self.status("bc", "unavailable")], "2026-11-14", "t")
        self.assertEqual(len(out["jobs"]), 1)
        self.assertEqual(out["sources"][0]["carried"], 1)
        self.assertEqual(out["sources"][0]["lastOk"], "2026-11-13")

    def test_stale_jobs_are_not_carried_forever(self):
        prev = {"jobs": [self.job(firstSeen="2026-10-01", lastSeen="2026-10-02")], "sources": []}
        out = merge(prev, [], [self.status("bc", "unavailable")], "2026-11-14", "t")
        self.assertEqual(out["jobs"], [])

    def test_first_seen_survives_refresh(self):
        prev = {"jobs": [self.job(firstSeen="2026-11-05", lastSeen="2026-11-13")], "sources": []}
        out = merge(prev, [self.job()], [self.status("bc", "ok")], "2026-11-14", "t")
        self.assertEqual(out["jobs"][0]["firstSeen"], "2026-11-05")

    def test_dedupe_prefers_portal_over_job_bank(self):
        copy = self.job(id="b", source="jb-ontario")
        self.assertEqual(dedupe([copy, self.job()])[0]["source"], "bc")


if __name__ == "__main__":
    unittest.main()
