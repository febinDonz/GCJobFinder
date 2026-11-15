"""Per-portal parsers, ported from the original GCJobFinder updater.

Each parser takes (source, text) and returns normalized job dicts via make_job.
Ontario is intentionally not scraped here: GOjobs serves a CAPTCHA to automated
clients, so Ontario postings come from Job Bank (see jobbank.py).
"""
from __future__ import annotations

import html
import re
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

from .common import (MAX_JOBS_PER_SOURCE, REGION_BY_CODE, TODAY, clean, fetch,
                     has_access_challenge, make_job)


def markdown_links(text):
    return re.findall(r"\[([^\]]+)\]\((https?://[^)\s]+)(?:\s+[^)]*)?\)", text)


def parse_bc(source, text):
    jobs = []
    for line in text.splitlines():
        if "|" not in line or "[" not in line:
            continue
        cells = [cell.strip() for cell in line.split("|") if cell.strip()]
        if len(cells) < 8 or re.search(r"Ministry/Organization|Req\. #|Job Title", cells[0], re.I):
            continue
        link_index = next((i for i, cell in enumerate(cells) if re.search(r"\]\(https?://", cell)), -1)
        if link_index < 0:
            continue
        links = markdown_links(cells[link_index])
        if not links:
            continue
        title, posting_url = links[0]
        jobs.append(make_job(
            source, title, cells[0], cells[5], posting_url,
            date=cells[6], closing_date=cells[7] if len(cells) > 7 else "",
            description=f"{cells[0]} opportunity in {cells[5]}",
            arrangement="Hybrid" if "hybrid" in cells[4].lower() else "On-site",
        ))
    return [job for job in jobs if job][:MAX_JOBS_PER_SOURCE]


def parse_gc(source, text):
    entries = []
    current = None
    for raw_line in text.splitlines():
        line = clean(raw_line)
        if not line:
            continue
        if re.match(r"^\d+\.\s*Closing date:", line, re.I) or re.match(r"^Closing date:", line, re.I):
            if current:
                entries.append(current)
            current = [line]
        elif current and line not in ("* * *", "---"):
            current.append(line)
    if current:
        entries.append(current)

    jobs = []
    for entry in entries:
        closing = next((re.search(r"\d{4}-\d{2}-\d{2}", line).group(0)
                        for line in entry if "Closing date:" in line and re.search(r"\d{4}-\d{2}-\d{2}", line)), "")
        content = [line for line in entry[1:] if line and not line.startswith("*")]
        if not content or (closing and closing < TODAY):
            continue
        org_and_unit = content[0]
        agency = re.split(r"\s+-\s+", org_and_unit, maxsplit=1)[0]
        location = next((line for line in content[1:] if re.search(
            r"\b(AB|BC|MB|NB|NL|NT|NS|NU|ON|PE|QC|SK|YT|Various Locations|Canada-wide)\b", line
        )), "Canada-wide")
        salary = next((line for line in content if line.startswith("$")), "")
        unit = org_and_unit[len(agency):].strip(" -")
        title = f"{agency} — {unit}" if unit else f"Open positions — {agency}"
        jobs.append(make_job(
            source,
            title,
            agency,
            location,
            source[4],
            date="",
            closing_date=closing,
            salary=salary if unit else "",
            description=f"{org_and_unit}. {location}" if unit else f"Current openings may be available with {agency} in {location}.",
            direct=False,
            identity="|".join((org_and_unit, location, salary, closing)) if unit else f"generic|{agency}|{location}",
            region_override=next(
                (value for code, value in REGION_BY_CODE.items() if re.search(rf"\b{code}\b", location)),
                "Canada",
            ),
        ))
    return [job for job in jobs if job][:MAX_JOBS_PER_SOURCE]


def parse_saskatchewan(source, text):
    jobs = []
    for title_and_description, posting_url in markdown_links(text):
        if "/job/" not in posting_url:
            continue
        title = re.sub(r"\s+This job\s+.*$", "", title_and_description, flags=re.I)
        jobs.append(make_job(
            source, title, source[1], "Saskatchewan", posting_url,
            description=title_and_description,
        ))
    return [job for job in jobs if job][:MAX_JOBS_PER_SOURCE]


def parse_manitoba(source, raw_xml):
    root = ET.fromstring(raw_xml)
    jobs = []
    for item in root.findall(".//item"):
        title = clean(item.findtext("title", ""))
        detail_url = (item.findtext("link", "") or "").strip()
        raw_description = html.unescape(item.findtext("description", ""))
        description = clean(raw_description)
        raw_fields = {
            key: clean(value)
            for key, value in re.findall(r"<strong>([^<]+)</strong>\s*:\s*([^<]+)", raw_description, flags=re.I)
        }
        fields = {
            clean(key).lower().replace("´", "'").replace("’", "'"): value
            for key, value in raw_fields.items()
        }
        ad_number = fields.get("ad no", "") or fields.get("numéro de l'annonce", "")
        department = fields.get("department", "") or fields.get("ministère", "")
        location = fields.get("location(s)", "") or fields.get("lieu(s)", "") or "Manitoba"
        salary = fields.get("salary(s)", "") or fields.get("salaire(s)", "")
        posted_date = fields.get("posted date", "") or fields.get("date d'affichage", "")
        closing_date = fields.get("closing date", "") or fields.get("date de clôture", "")
        jobs.append(make_job(
            source, title, department or source[1], location, detail_url,
            date=posted_date, closing_date=closing_date, salary=salary,
            description=description,
            identity=ad_number,
        ))
    return [job for job in jobs if job][:MAX_JOBS_PER_SOURCE]



class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
        self.anchor = None
        self.links = []
        self.link = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = {"text": "", "url": ""}
            self.row.append(self.cell)
        elif tag == "a":
            self.anchor = {"text": "", "url": attrs.get("href", "")}
            if self.cell is not None:
                self.cell["url"] = self.anchor["url"]

    def handle_data(self, data):
        if self.cell is not None:
            self.cell["text"] += data
        if self.anchor is not None:
            self.anchor["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.anchor is not None:
            self.links.append(self.anchor)
            self.anchor = None
        elif tag in ("td", "th"):
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if any(cell["text"].strip() for cell in self.row):
                self.rows.append(self.row)
            self.row = None


def parse_nwt(source, html_text):
    parser = TableParser()
    parser.feed(html_text)
    jobs = []
    for link in parser.links:
        href = link["url"]
        if href and re.search(r"/careers/(?:en/)?job/\d+", href, re.I):
            detail_url = urllib.parse.urljoin(source[4], href)
            title = clean(link["text"])
            jobs.append(make_job(
                source, title, source[1], "Northwest Territories", detail_url,
                description=title,
            ))
    return [job for job in jobs if job][:MAX_JOBS_PER_SOURCE]


def parse_quebec(source, text):
    jobs = []
    pattern = re.compile(
        r"Date de fin de la période de publication\s+(?P<date>\d{4}-\d{2}-\d{2})"
        r".*?Titre\s+(?P<title>.+?)\s+Ministère ou organisme\s+(?P<agency>.+?)"
        r"\s+Numéro\s+(?P<number>[A-Z0-9-]+)",
        flags=re.I | re.S,
    )
    for match in pattern.finditer(text):
        title = clean(match.group("title"))
        number = match.group("number")
        # The portal's public listing exposes the competition number but not a stable
        # individual URL in its text view, so link to its live results page.
        jobs.append(make_job(
            source, title, match.group("agency"), "Quebec", source[4],
            date="", closing_date=match.group("date"),
            description=f"Competition {number} • {match.group('agency')}", direct=False,
        ))
    return [job for job in jobs if job][:MAX_JOBS_PER_SOURCE]


def parse_nb(source, text):
    jobs = []
    pattern = re.compile(
        r"\[([^\]]+)\]\(javascript:__doPostBack\('[^']+'\s*,\s*'[^']*'\)\)\s*"
        r"([A-Z0-9-]+)\s+([A-Z]{2,6})\s+(.+?)\s+"
        r"((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4})",
        flags=re.I,
    )
    for match in pattern.finditer(text):
        title, number, department, location, closing_date = match.groups()
        # New Brunswick posts use a WebForms postback for detail; the competition
        # list is the official public fallback until a stable detail URL is exposed.
        jobs.append(make_job(
            source, title, f"{source[1]} — {department}", location,
            source[4], date="", closing_date=closing_date,
            description=f"Competition {number} • {department}", direct=False, identity=number,
        ))
    return [job for job in jobs if job][:MAX_JOBS_PER_SOURCE]


def parse_nova_scotia(source, text):
    jobs = []
    for title, posting_url in markdown_links(text):
        if "jobs.novascotia.ca/job-invite/" not in posting_url:
            continue
        jobs.append(make_job(
            source, title, source[1], "Nova Scotia", posting_url, description=title,
        ))
    return [job for job in jobs if job][:MAX_JOBS_PER_SOURCE]


def parse_alberta(source, text):
    jobs = []
    for line in text.splitlines():
        if "|" not in line or "[" not in line:
            continue
        links = [(title, url) for title, url in markdown_links(line) if "/job/" in url]
        if not links:
            continue
        cells = [clean(cell) for cell in line.split("|") if clean(cell)]
        title, posting_url = links[0]
        location = cells[1] if len(cells) > 2 else "Alberta"
        posted_date = cells[2] if len(cells) > 2 else ""
        jobs.append(make_job(
            source, title, source[1], location, posting_url,
            date=posted_date, description=f"{title} in {location}",
        ))
    if jobs:
        return [job for job in jobs if job][:MAX_JOBS_PER_SOURCE]

    parser = TableParser()
    parser.feed(text)
    jobs = []
    for link in parser.links:
        href = link["url"] or ""
        if re.search(r"/job/|/job-invite/", href, re.I):
            jobs.append(make_job(
                source, link["text"], source[1], "Alberta",
                urllib.parse.urljoin(source[4], href), description=link["text"],
            ))
    if jobs:
        return [job for job in jobs if job][:MAX_JOBS_PER_SOURCE]

    # SuccessFactors exposes its live job search through the category/keyword
    # search page rather than embedding postings in its top-level page.
    for link in parser.links:
        href, title = link["url"], link["text"]
        if re.search(r"/job/|/job-invite/", href, re.I):
            jobs.append(make_job(
                source, title, source[1], "Alberta",
                urllib.parse.urljoin(source[4], href), description=title,
            ))
    return [job for job in jobs if job][:MAX_JOBS_PER_SOURCE]


def parse_generic(source, text):
    jobs = []
    for title, posting_url in markdown_links(text):
        if any(token in posting_url.lower() for token in ("/job/", "/jobs/", "/posting/", "/competition/")):
            jobs.append(make_job(
                source, title, source[1], source[3], posting_url, description=title,
            ))
    return [job for job in jobs if job][:MAX_JOBS_PER_SOURCE]


# (key, label, government level, region, portal URL, parser)
SOURCES = [
    ("gc-jobs", "GC Jobs (federal public service)", "Federal", "Canada",
     "https://emploisfp-psjobs.cfp-psc.gc.ca/psrs-srfp/applicant/page2440?fromMenu=true", "gc"),
    ("bc", "BC Public Service", "Provincial", "British Columbia",
     "https://bcpublicservice.hua.hrsmart.com/hr/ats/JobSearch/viewAll", "bc"),
    ("alberta", "Alberta Public Service", "Provincial", "Alberta",
     "https://jobpostings.alberta.ca/search/?q=", "alberta"),
    ("saskatchewan", "Government of Saskatchewan", "Provincial", "Saskatchewan",
     "https://careers.saskatchewan.ca/", "saskatchewan"),
    ("manitoba", "Manitoba Government", "Provincial", "Manitoba",
     "https://jobsearch.gov.mb.ca/rss/newJobPostingsFeed.rss", "manitoba"),
    ("quebec", "Quebec Public Service", "Provincial", "Quebec",
     "https://recrutement.carrieres.gouv.qc.ca/", "quebec"),
    ("new-brunswick", "Government of New Brunswick", "Provincial", "New Brunswick",
     "https://www.ere.gnb.ca/competition.aspx?culture=en-CA", "new-brunswick"),
    ("nova-scotia", "Government of Nova Scotia", "Provincial", "Nova Scotia",
     "https://jobs.novascotia.ca/", "nova-scotia"),
    ("pei", "Government of Prince Edward Island", "Provincial", "Prince Edward Island",
     "https://www.princeedwardisland.ca/en/topic/employment-opportunities", "generic"),
    ("newfoundland", "Government of Newfoundland and Labrador", "Provincial", "Newfoundland and Labrador",
     "https://www.hiring.gov.nl.ca/Competitions/Public", "generic"),
    ("yukon", "Government of Yukon", "Territorial", "Yukon",
     "https://yukon.ca/en/employment", "generic"),
    ("nwt", "Government of the Northwest Territories", "Territorial", "Northwest Territories",
     "https://www.gov.nt.ca/careers/en/search/job", "nwt"),
    ("nunavut", "Government of Nunavut", "Territorial", "Nunavut",
     "https://gov.nu.ca/en/careers", "generic"),
]

PARSERS = {
    "gc": parse_gc,
    "bc": parse_bc,
    "alberta": parse_alberta,
    "saskatchewan": parse_saskatchewan,
    "manitoba": parse_manitoba,
    "quebec": parse_quebec,
    "new-brunswick": parse_nb,
    "nova-scotia": parse_nova_scotia,
    "nwt": parse_nwt,
    "generic": parse_generic,
}

# These two serve clean XML/HTML directly; the rest go through a text reader.
DIRECT_FETCH = ("manitoba", "nwt")


def collect_portal(source):
    """Fetch and parse one portal. Never raises: failures become a status."""
    key, label, level, region, url, parser_name = source
    base = {"key": key, "label": label, "government": level, "region": region, "portalUrl": url}
    if parser_name == "link_only":
        return [], {**base, "status": "link_only", "count": 0}
    try:
        body = fetch(url, proxy=parser_name not in DIRECT_FETCH)
        jobs = PARSERS[parser_name](source, body)
        if jobs:
            return jobs, {**base, "status": "ok", "count": len(jobs)}
        status = "blocked_or_challenge" if has_access_challenge(body) else "no_listings_parsed"
        return [], {**base, "status": status, "count": 0}
    except (urllib.error.URLError, TimeoutError, ValueError, ET.ParseError) as error:
        return [], {**base, "status": "unavailable", "error": str(error)[:240], "count": 0}
    except Exception as error:  # one broken portal must not stop the others
        return [], {**base, "status": "parse_error", "error": str(error)[:240], "count": 0}
