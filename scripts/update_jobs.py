#!/usr/bin/env python3
"""Refresh public government job listings into the static jobs.json feed."""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import http.cookiejar
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "jobs.json"
TIMEOUT_SECONDS = 45
MAX_JOBS_PER_SOURCE = 50
TODAY = dt.datetime.now(dt.timezone.utc).date().isoformat()
REGION_BY_CODE = {
    "AB": "Alberta",
    "BC": "British Columbia",
    "MB": "Manitoba",
    "NB": "New Brunswick",
    "NL": "Newfoundland and Labrador",
    "NT": "Northwest Territories",
    "NS": "Nova Scotia",
    "NU": "Nunavut",
    "ON": "Ontario",
    "PE": "Prince Edward Island",
    "QC": "Quebec",
    "SK": "Saskatchewan",
    "YT": "Yukon",
}


SOURCES = [
    ("gc-jobs", "GC Jobs", "Federal", "Canada",
     "https://emploisfp-psjobs.cfp-psc.gc.ca/psrs-srfp/applicant/page2440?fromMenu=true", "gc"),
    ("bc", "BC Public Service", "Provincial", "British Columbia",
     "https://bcpublicservice.hua.hrsmart.com/hr/ats/JobSearch/viewAll", "bc"),
    ("alberta", "Alberta Public Service", "Provincial", "Alberta",
     "https://jobpostings.alberta.ca/search/?q=", "alberta"),
    ("saskatchewan", "Government of Saskatchewan", "Provincial", "Saskatchewan",
     "https://careers.saskatchewan.ca/", "saskatchewan"),
    ("manitoba", "Manitoba Government", "Provincial", "Manitoba",
     "https://jobsearch.gov.mb.ca/rss/newJobPostingsFeed.rss", "manitoba"),
    ("ontario", "Ontario Public Service", "Provincial", "Ontario",
     "https://www.gojobs.gov.on.ca/Search.aspx", "ontario"),
    ("quebec", "Québec Public Service", "Provincial", "Quebec",
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


def fetch(url: str, *, proxy: bool = True) -> str:
    if proxy:
        parsed = urllib.parse.urlsplit(url)
        url = f"https://r.jina.ai/http://{parsed.netloc}{parsed.path}"
        if parsed.query:
            url += f"?{parsed.query}"
    for attempt in range(3):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "GCJobFinder/1.0 (public government job listings)"},
        )
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                body = response.read()
                return body.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2:
                raise
        time.sleep(attempt + 1)
    raise RuntimeError(f"Unable to fetch {url}")


def clean(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:90] or "job"


def parse_date(value: str) -> str:
    value = clean(value)
    for form in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return dt.datetime.strptime(value, form).date().isoformat()
        except ValueError:
            pass
    return TODAY


def make_job(source, title, agency, location, url, *, date="", closing_date="", salary="", description="", arrangement="On-site", direct=True, identity="", region_override=""):
    key, label, level, source_region, source_url, _ = source
    title = clean(title)
    agency = clean(agency or label)
    location = clean(location or source_region)
    region = clean(region_override or source_region)
    if not title or not url or not url.startswith(("https://", "http://")):
        return None
    posted = parse_date(date)
    closing = parse_date(closing_date) if closing_date else ""
    stable_id = hashlib.sha1(f"{key}|{agency}|{title}|{url}|{identity}".encode("utf-8")).hexdigest()[:12]
    return {
        "id": f"live-{slug(key)}-{stable_id}",
        "title": title,
        "agency": agency,
        "government": level,
        "region": region,
        "location": location,
        "type": "Full-time",
        "level": "Public service",
        "salaryText": clean(salary) or "See official posting",
        "posted": posted,
        "postedText": f"Closes {closing} • {label}" if closing else f"Live posting • {label}",
        "closingDate": closing,
        "arrangement": arrangement if arrangement in ("Remote", "Hybrid", "On-site") else "On-site",
        "student": "student" in title.lower(),
        "sourceLabel": label,
        "sourceUrl": url,
        "directPosting": direct,
        "description": clean(description) or f"Current opportunity with {agency} in {location}."
    }


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
            date=TODAY,
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


class OntarioSearchFormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.form_attrs = None
        self.in_form = False
        self.seen_form = False
        self.controls = []
        self.select = None
        self.option = None
        self.button = None
        self.search_button = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form" and not self.seen_form:
            self.form_attrs = attrs
            self.in_form = True
            self.seen_form = True
        elif not self.in_form:
            return
        elif tag == "input":
            self.controls.append(("input", attrs))
            if attrs.get("type", "").lower() == "submit" and re.search(
                r"search", attrs.get("value", ""), re.I
            ):
                self.search_button = attrs
        elif tag == "select":
            self.select = {"attrs": attrs, "options": []}
        elif tag == "option" and self.select is not None:
            self.option = {"attrs": attrs, "text": ""}
        elif tag == "button":
            self.button = {"attrs": attrs, "text": ""}

    def handle_data(self, data):
        if self.option is not None:
            self.option["text"] += data
        if self.button is not None:
            self.button["text"] += data

    def handle_endtag(self, tag):
        if tag == "option" and self.option is not None:
            self.select["options"].append(self.option)
            self.option = None
        elif tag == "select" and self.select is not None:
            attrs = self.select["attrs"]
            selected = next(
                (option for option in self.select["options"] if "selected" in option["attrs"]),
                self.select["options"][0] if self.select["options"] else None,
            )
            if attrs.get("name") and selected is not None:
                value = selected["attrs"].get("value", clean(selected["text"]))
                self.controls.append(("value", (attrs["name"], value)))
            self.select = None
        elif tag == "button" and self.button is not None:
            attrs = self.button["attrs"]
            if attrs.get("type", "submit").lower() == "submit" and re.search(
                r"search", clean(self.button["text"]) or attrs.get("value", ""), re.I
            ):
                self.search_button = attrs
            self.button = None
        elif tag == "form":
            self.in_form = False

    def post_data(self):
        fields = []
        for kind, control in self.controls:
            if kind == "value":
                fields.append(control)
                continue
            name = control.get("name")
            input_type = control.get("type", "text").lower()
            if not name or input_type in ("submit", "button", "reset", "file"):
                continue
            if input_type in ("checkbox", "radio") and "checked" not in control:
                continue
            fields.append((name, control.get("value", "")))

        if self.search_button is None:
            raise ValueError("Ontario search form has no usable Search button")
        name = self.search_button.get("name")
        if name:
            fields.append((name, self.search_button.get("value", "")))
        onclick = self.search_button.get("onclick", "")
        postback = re.search(
            r"__doPostBack\(['\"]([^'\"]*)['\"]\s*,\s*['\"]([^'\"]*)['\"]\)",
            onclick,
        )
        if postback:
            fields.extend((
                ("__EVENTTARGET", postback.group(1)),
                ("__EVENTARGUMENT", postback.group(2)),
            ))
        return fields


def has_access_challenge(text):
    return bool(re.search(
        r"captcha|security verification|request cannot be processed|access denied|"
        r"validate\.perfdrive\.com|captcha\.perfdrive\.com",
        text,
        re.I,
    ))


def fetch_ontario_search(url):
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
    )
    headers = {
        "User-Agent": "GCJobFinder/1.0 (public government job listings)",
        "Accept": "text/html,application/xhtml+xml",
    }
    with opener.open(urllib.request.Request(url, headers=headers), timeout=TIMEOUT_SECONDS) as response:
        page = response.read().decode("utf-8", errors="replace")
        page_url = response.geturl()
    if has_access_challenge(page):
        raise PermissionError("Ontario careers portal returned an access challenge")

    form = OntarioSearchFormParser()
    form.feed(page)
    if form.form_attrs is None or form.form_attrs.get("method", "get").lower() != "post":
        raise ValueError("Ontario careers page did not expose its expected search form")
    post_url = urllib.parse.urljoin(page_url, form.form_attrs.get("action") or page_url)
    request = urllib.request.Request(
        post_url,
        data=urllib.parse.urlencode(form.post_data()).encode("utf-8"),
        headers={
            **headers,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": page_url,
        },
        method="POST",
    )
    with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
        result = response.read().decode("utf-8", errors="replace")
    if has_access_challenge(result):
        raise PermissionError("Ontario careers portal returned an access challenge")
    return result


def parse_ontario(source, text):
    parser = TableParser()
    parser.feed(text)
    jobs = []
    for row in parser.rows:
        row_text = clean(" ".join(cell["text"] for cell in row))
        for cell in row:
            posting_url = cell["url"]
            if not posting_url or not re.search(
                r"(?:jobdetails|jobdetail|jobposting|jobid=|job_id=)",
                posting_url,
                re.I,
            ):
                continue
            title = clean(cell["text"])
            if not title or re.search(r"^(?:job title|title|details)$", title, re.I):
                continue
            detail_url = urllib.parse.urljoin(source[4], posting_url)
            jobs.append(make_job(
                source, title, source[1], "Ontario", detail_url,
                description=row_text,
            ))
    return [job for job in jobs if job]


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
            date=TODAY, closing_date=match.group("date"),
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
            source[4], date=TODAY, closing_date=closing_date,
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


PARSERS = {
    "gc": parse_gc,
    "bc": parse_bc,
    "alberta": parse_alberta,
    "saskatchewan": parse_saskatchewan,
    "manitoba": parse_manitoba,
    "ontario": parse_ontario,
    "quebec": parse_quebec,
    "new-brunswick": parse_nb,
    "nova-scotia": parse_nova_scotia,
    "nwt": parse_nwt,
    "generic": parse_generic,
}


def collect(source):
    key, label, _, _, url, parser_name = source
    try:
        body = fetch_ontario_search(url) if parser_name == "ontario" else fetch(
            url, proxy=parser_name not in ("manitoba", "nwt")
        )
        parser = PARSERS[parser_name]
        jobs = parser(source, body) if parser else []
        if jobs:
            return jobs, {"key": key, "label": label, "status": "ok", "count": len(jobs)}
        if has_access_challenge(body):
            return [], {"key": key, "label": label, "status": "blocked_or_challenge", "count": 0}
        return [], {"key": key, "label": label, "status": "no_listings_parsed", "count": 0}
    except PermissionError as error:
        return [], {"key": key, "label": label, "status": "blocked_or_challenge", "error": str(error), "count": 0}
    except (urllib.error.URLError, TimeoutError, ValueError, ET.ParseError) as error:
        return [], {"key": key, "label": label, "status": "unavailable", "error": str(error)[:240], "count": 0}
    except Exception as error:  # Keep one broken source from blocking other public feeds.
        return [], {"key": key, "label": label, "status": "parse_error", "error": str(error)[:240], "count": 0}


def main():
    jobs = []
    statuses = []
    with ThreadPoolExecutor(max_workers=7) as pool:
        futures = [pool.submit(collect, source) for source in SOURCES]
        for future in as_completed(futures):
            source_jobs, status = future.result()
            jobs.extend(source_jobs)
            statuses.append(status)

    jobs = list({job["id"]: job for job in jobs}.values())
    jobs.sort(key=lambda job: job["posted"], reverse=True)
    if not jobs:
        print("No live postings were collected; keeping the existing jobs.json.", file=sys.stderr)
        return 1

    result = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "scheduleTimezone": "UTC",
        "jobs": jobs,
        "sources": sorted(statuses, key=lambda source: source["key"]),
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(jobs)} live postings from {sum(s['count'] > 0 for s in statuses)} sources.")
    for status in sorted(statuses, key=lambda source: source["key"]):
        print(f"{status['label']}: {status['status']} ({status['count']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
