"""Shared helpers: HTTP, text cleanup and the normalized job record."""
from __future__ import annotations

import datetime as dt
import hashlib
import html
import re
import time
import urllib.error
import urllib.parse
import urllib.request

TODAY = dt.datetime.now(dt.timezone.utc).date().isoformat()
TIMEOUT_SECONDS = 45
MAX_JOBS_PER_SOURCE = 500
USER_AGENT = "CanadaGovJobs/1.0 (public-sector job aggregator; honours robots.txt)"

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

_CHALLENGE = re.compile(
    r"captcha|security verification|request cannot be processed|access denied|"
    r"validate\.perfdrive\.com|captcha\.perfdrive\.com",
    re.I,
)
_LINK_TEXT = {"here", "apply", "apply now", "read more", "more", "details", "view", "click here", "search"}
_STUDENT = re.compile(r"\b(student|co-?op|intern(ship)?|fswep)\b", re.I)


def has_access_challenge(text: str) -> bool:
    return bool(_CHALLENGE.search(text or ""))


def fetch(url: str, *, proxy: bool = True) -> str:
    """GET a page. With proxy=True the page is read through r.jina.ai, which
    returns readable text for JavaScript-heavy portals."""
    if proxy:
        parsed = urllib.parse.urlsplit(url)
        url = f"https://r.jina.ai/http://{parsed.netloc}{parsed.path}"
        if parsed.query:
            url += f"?{parsed.query}"
    for attempt in range(3):
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return response.read().decode("utf-8", errors="replace")
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
    """Return an ISO date, or '' when the text holds no date we understand."""
    value = clean(value)
    found = re.search(r"\d{4}-\d{2}-\d{2}", value)
    if found:
        return found.group(0)
    for form in ("%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%d %B %Y"):
        try:
            return dt.datetime.strptime(value, form).date().isoformat()
        except ValueError:
            pass
    found = re.search(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2},\s+\d{4}",
        value,
    )
    if found:
        return parse_date(found.group(0))
    return ""


def make_job(source, title, agency, location, url, *, date="", closing_date="", salary="",
             description="", arrangement="On-site", direct=True, identity="", region_override=""):
    """Build one normalized job record. Returns None when title or URL is unusable."""
    key, label, level, source_region, _portal, _parser = source
    title = clean(title)
    employer = clean(agency or label)
    location = clean(location or source_region)
    region = clean(region_override or source_region)
    if not title or not url or not url.startswith(("https://", "http://")):
        return None
    if title.lower() in _LINK_TEXT:  # a bare "here" or "apply" link, not a job title
        return None
    stable_id = hashlib.sha1(f"{key}|{employer}|{title}|{url}|{identity}".encode("utf-8")).hexdigest()[:12]
    return {
        "id": f"{slug(key)}-{stable_id}",
        "title": title,
        "employer": employer,
        "government": level,
        "region": region,
        "location": location,
        "salary": clean(salary),
        "posted": parse_date(date),
        "closing": parse_date(closing_date) if closing_date else "",
        "url": url,
        "direct": bool(direct),
        "source": key,
        "sourceLabel": label,
        "arrangement": arrangement if arrangement in ("Remote", "Hybrid", "On-site") else "On-site",
        "student": bool(_STUDENT.search(title)),
        "description": clean(description) or f"{employer}, {location}",
    }
