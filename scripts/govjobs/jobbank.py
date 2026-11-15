"""Job Bank adapter.

Job Bank (jobbank.gc.ca) is the Government of Canada's national job board.
Several employers cross-post there, including the Ontario Public Service, whose
own portal (GOjobs) blocks automated clients behind a CAPTCHA. We never try to
bypass that; Job Bank is the legitimate public route to Ontario postings.

Coverage caveat: Job Bank shows the postings an employer chose to publish
there. It can be a subset of what the employer's own portal lists.
"""
from __future__ import annotations

import re
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser

from .common import (MAX_JOBS_PER_SOURCE, REGION_BY_CODE, USER_AGENT, clean,
                     has_access_challenge, make_job, TIMEOUT_SECONDS)

BASE = "https://www.jobbank.gc.ca"
MAX_PAGES = 20
PAUSE_SECONDS = 1.0

# Each group becomes one row in the "sources" table.
GROUPS = [
    {"key": "jb-ontario", "label": "Ontario Public Service (via Job Bank)", "government": "Provincial",
     "region": "Ontario", "employers": ["Ontario Public Service"], "match": ["ontario public service"]},
    {"key": "jb-newfoundland", "label": "Newfoundland and Labrador (via Job Bank)", "government": "Provincial",
     "region": "Newfoundland and Labrador", "employers": ["Government of Newfoundland and Labrador"],
     "match": ["newfoundland and labrador"]},
    {"key": "jb-pei", "label": "Prince Edward Island (via Job Bank)", "government": "Provincial",
     "region": "Prince Edward Island", "employers": ["Government of Prince Edward Island"],
     "match": ["prince edward island"]},
    {"key": "jb-new-brunswick", "label": "New Brunswick (via Job Bank)", "government": "Provincial",
     "region": "New Brunswick", "employers": ["Government of New Brunswick"], "match": ["new brunswick"]},
    {"key": "jb-nova-scotia", "label": "Nova Scotia (via Job Bank)", "government": "Provincial",
     "region": "Nova Scotia", "employers": ["Government of Nova Scotia"], "match": ["nova scotia"]},
    {"key": "jb-yukon", "label": "Yukon (via Job Bank)", "government": "Territorial",
     "region": "Yukon", "employers": ["Government of Yukon"], "match": ["yukon"]},
    {"key": "jb-nunavut", "label": "Nunavut (via Job Bank)", "government": "Territorial",
     "region": "Nunavut", "employers": ["Government of Nunavut"], "match": ["nunavut"]},
    {"key": "jb-federal", "label": "Federal departments (via Job Bank)", "government": "Federal",
     "region": "Canada",
     "employers": ["Government of Canada", "Canada Revenue Agency", "Parks Canada", "Statistics Canada",
                   "Public Services and Procurement Canada", "Canada Border Services Agency",
                   "Royal Canadian Mounted Police", "Department of National Defence",
                   "Correctional Service Canada", "Employment and Social Development Canada"],
     "match": []},
]

POSTING_RE = re.compile(r"/jobsearch/jobposting/(\d+)")
DATE_RE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+\d{1,2},\s+\d{4}")
PLACE_RE = re.compile(r"\(([A-Z]{2})\)")
NOISE = re.compile(
    r"^(new|on[- ]site|hybrid|remote|telework|posted on job bank|direct apply|"
    r"save to favou?rites?|temporary|permanent|full time|part time|\d+ days? ago)$", re.I)
SOURCE_LINE = re.compile(r"^(?:job number|source|job bank|whoplusyou)\b", re.I)
# Source labels that sit beside the real title in each card. Seen in the first live run:
# "This job was posted directly by the employer on Job Bank." and "Jobs.gc.ca".
LABEL_LINE = re.compile(
    r"posted directly|posted by|this job was|jobs\.gc\.ca|^\w+\.gc\.ca$|"
    r"^(?:apply|view|details|more info|share|print)\b|^job bank\b|^#?\d{6,}$", re.I)


class _CardParser(HTMLParser):
    """Collect each result link and the text inside it, one line per element."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cards = []
        self._cur = None

    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get("href") or ""
        found = POSTING_RE.search(href) if tag == "a" else None
        if found and self._cur is None:
            self._cur = {"id": found.group(1), "lines": [""]}
        elif self._cur is not None:
            self._cur["lines"].append("")

    def handle_endtag(self, tag):
        if self._cur is None:
            return
        if tag == "a":
            self.cards.append(self._cur)
            self._cur = None
        else:
            self._cur["lines"].append("")

    def handle_data(self, data):
        if self._cur is not None:
            self._cur["lines"][-1] += data


def parse_results(page: str, group: dict, employer_query: str, source: tuple):
    """Turn one Job Bank results page into job dicts. Returns (jobs, ids_seen)."""
    parser = _CardParser()
    parser.feed(page)
    best = {}
    for card in parser.cards:
        if card["id"] not in best or len(card["lines"]) > len(best[card["id"]]["lines"]):
            best[card["id"]] = card
    jobs = []
    for job_id, card in best.items():
        lines = [clean(line) for line in card["lines"] if clean(line)]
        lines = [line for line in lines
                 if not NOISE.match(line) and not SOURCE_LINE.match(line) and not LABEL_LINE.search(line)]
        date = next((m.group(0) for m in (DATE_RE.search(line) for line in lines) if m), "")
        place = next((line for line in lines if PLACE_RE.search(line)), "")
        place = re.sub(r"^Location\s*:?\s*", "", place)
        salary = next((line for line in lines if "$" in line), "")
        salary = re.sub(r"^Salary\s*:?\s*", "", salary)
        employer = next((line for line in lines
                         if any(token in line.lower() for token in group["match"])), "")
        employer = re.sub(r"^Employer\s*:?\s*", "", employer) or employer_query
        used = {date and next((l for l in lines if date in l), ""), place, salary, employer}
        title = next((line for line in lines if line not in used and not DATE_RE.search(line)), "")
        title = re.sub(r"\s*Save to favou?rites?\s*$", "", title, flags=re.I)
        if not title:
            continue
        code = PLACE_RE.search(place)
        region = REGION_BY_CODE.get(code.group(1), group["region"]) if code else group["region"]
        job = make_job(
            source, title, employer, place or group["region"], f"{BASE}/jobsearch/jobposting/{job_id}",
            date=date, salary=salary, direct=True, identity=job_id, region_override=region)
        if job:
            jobs.append(job)
    return jobs, set(best)


_robots = None


def robots_allows(url: str) -> bool:
    global _robots
    if _robots is None:
        _robots = urllib.robotparser.RobotFileParser()
        try:
            request = urllib.request.Request(f"{BASE}/robots.txt", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                _robots.parse(response.read().decode("utf-8", errors="replace").splitlines())
        except (urllib.error.URLError, TimeoutError):
            _robots.parse([])  # robots.txt unreachable: nothing forbids us
    return _robots.can_fetch(USER_AGENT, url)


def _get(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read().decode("utf-8", errors="replace")


def search_url(employer: str, page: int) -> str:
    return f"{BASE}/jobsearch/jobsearch?{urllib.parse.urlencode({'empl': employer, 'sort': 'D', 'page': page})}"


def collect_group(group: dict):
    """Collect every employer in a group. Never raises."""
    source = (group["key"], group["label"], group["government"], group["region"], BASE, "jobbank")
    base = {"key": group["key"], "label": group["label"], "government": group["government"],
            "region": group["region"], "portalUrl": search_url(group["employers"][0], 1)}
    jobs, errors, challenged, blocked = {}, [], False, False
    for employer in group["employers"]:
        seen = set()
        for page_number in range(1, MAX_PAGES + 1):
            url = search_url(employer, page_number)
            if not robots_allows(url):
                blocked = True
                break
            try:
                page = _get(url)
            except (urllib.error.URLError, TimeoutError) as error:
                errors.append(str(error)[:160])
                break
            if has_access_challenge(page):
                challenged = True
                break
            found, ids = parse_results(page, group, employer, source)
            if not ids or ids <= seen:
                break
            seen |= ids
            for job in found:
                jobs[job["id"]] = job
            time.sleep(PAUSE_SECONDS)
        time.sleep(PAUSE_SECONDS)
    result = list(jobs.values())[:MAX_JOBS_PER_SOURCE]
    if result:
        return result, {**base, "status": "ok", "count": len(result)}
    if challenged:
        status = "blocked_or_challenge"
    elif blocked:
        status = "robots_disallowed"
    elif errors:
        status = "unavailable"
    else:
        status = "no_listings_parsed"
    out = {**base, "status": status, "count": 0}
    if errors:
        out["error"] = errors[0]
    return [], out
