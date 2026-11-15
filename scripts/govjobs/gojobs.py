"""Ontario Public Service postings from GOjobs (https://www.gojobs.gov.on.ca).

GOjobs lists nothing until its Search button is pressed, and the filter widgets
need JavaScript, so this drives a headless browser the way a person would:
open Search.aspx, tick every option in the required filters, press the Search
button at the bottom of the form, then read the results and page through them.

Rules this module keeps:
- robots.txt for GOjobs disallows only /alljobs.aspx and /ReadPDF.aspx. Neither is used.
- If the site answers with a CAPTCHA or access-denied page, it stops and reports
  "blocked_or_challenge". It never tries to get around a challenge.
- One browser session, a pause between page turns, and a page limit.

This was written without access to the live page. Selectors are deliberately
generic. Each run saves a screenshot and HTML excerpt to GOJOBS_DEBUG_DIR (the
workflow uploads them as an artifact) so a wrong guess is quick to correct.
"""
from __future__ import annotations

import os
import re
import time
import urllib.parse
from pathlib import Path

from .common import MAX_JOBS_PER_SOURCE, clean, has_access_challenge, make_job, USER_AGENT

SEARCH_URL = "https://www.gojobs.gov.on.ca/Search.aspx"
BASE = "https://www.gojobs.gov.on.ca/"
MAX_PAGES = 80
PAUSE_SECONDS = 60          # one results page per minute, to stay polite
TIME_BUDGET_SECONDS = 28 * 60
RESULTS_WAIT_SECONDS = 120
FILTER_IDS = ("ucRegion", "ucCity", "ucCategory", "ucCareers")

SOURCE = ("ontario-gojobs", "Ontario Public Service (GOjobs)", "Provincial", "Ontario", SEARCH_URL, "gojobs")

JOB_LINK = re.compile(r"(?:JobID|JobId|jobid)=(\d+)|/Apply\.aspx|JobDetail", re.I)
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|"
                     r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2},? \d{4})\b")
SALARY_RE = re.compile(r"\$\s?[\d,]+(?:\.\d+)?(?:\s*(?:-|to)\s*\$?\s?[\d,]+(?:\.\d+)?)?(?:\s*(?:per|/)\s*\w+)?", re.I)
CLOSING_RE = re.compile(r"(?:clos\w*|deadline|apply by)\D{0,12}(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|"
                        r"[A-Z][a-z]+\.? \d{1,2},? \d{4})", re.I)

# Runs in the page. Returns one record per job link with the text of its row/card.
COLLECT_JS = """
(pattern) => {
  const re = new RegExp(pattern, 'i');
  const out = [];
  for (const a of document.querySelectorAll('a[href]')) {
    if (!re.test(a.getAttribute('href'))) continue;
    const row = a.closest('tr, li, article, .job, .card, [class*="result" i]') || a.parentElement;
    out.push({href: a.href, title: (a.innerText || a.textContent || '').trim(),
              row: row ? (row.innerText || row.textContent || '') : ''});
  }
  return out;
}
"""

SELECT_ALL_JS = """
(ids) => {
  let touched = 0;
  for (const sel of document.querySelectorAll('select[multiple]')) {
    for (const o of sel.options) { o.selected = true; }
    sel.dispatchEvent(new Event('change', {bubbles: true}));
    touched += 1;
  }
  for (const id of ids) {
    const scope = document.querySelectorAll(`[id*="${id}"], [name*="${id}"]`);
    for (const node of scope) {
      const boxes = node.matches('input[type=checkbox]') ? [node] : node.querySelectorAll('input[type=checkbox]');
      for (const box of boxes) {
        if (!box.checked) box.click();
        touched += 1;
      }
    }
  }
  return touched;
}
"""


def job_id_from_url(url: str) -> str:
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    for key, values in query.items():
        if key.lower() == "jobid" and values:
            return values[0]
    return ""


def parse_rows(items: list) -> list:
    """Turn collected link records into job dicts (pure function, unit tested)."""
    seen, jobs = set(), []
    for item in items:
        url = urllib.parse.urljoin(BASE, item.get("href", ""))
        title = clean(item.get("title", ""))
        job_id = job_id_from_url(url)
        if not title or len(title) < 3 or title.lower() in {"apply", "apply now", "view", "details", "more", "here"}:
            continue
        key = job_id or url
        if key in seen:
            continue
        seen.add(key)
        row = item.get("row", "") or ""
        lines = [clean(line) for line in re.split(r"[\r\n\t]+", row) if clean(line)]
        closing = CLOSING_RE.search(row)
        dates = [m.group(1) for m in DATE_RE.finditer(row)]
        posted = next((d for d in dates if not closing or d != closing.group(1)), "")
        salary = SALARY_RE.search(row)
        place = next((line for line in lines if line != title and re.search(r"\(ON\)|, ON\b|Ontario", line)), "")
        ministry = next((line for line in lines if re.search(r"\b(Ministry|Office|Agency|Commission|Secretariat)\b", line)
                         and line != title), "")
        job = make_job(SOURCE, title, ministry or "Ontario Public Service", place or "Ontario", url,
                       date=posted, closing_date=closing.group(1) if closing else "",
                       salary=salary.group(0) if salary else "", direct=True,
                       identity=job_id, description=" | ".join(l for l in lines if l != title)[:300])
        if job:
            jobs.append(job)
    return jobs


def _save_debug(page, name: str):
    folder = os.environ.get("GOJOBS_DEBUG_DIR")
    if not folder:
        return
    try:
        Path(folder).mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(Path(folder) / f"{name}.png"), full_page=True)
        (Path(folder) / f"{name}.html").write_text(page.content()[:400000], encoding="utf-8")
    except Exception:  # debugging aid only
        pass


def _press_search(page) -> bool:
    """Press the Search button at the bottom of the form."""
    pattern = re.compile(r"^\s*search\s*$", re.I)
    for locator in (page.get_by_role("button", name=pattern),
                    page.locator("input[type=submit], input[type=button], button, a").filter(has_text=pattern),
                    page.locator("input[type=submit][value*='earch' i], input[type=button][value*='earch' i]")):
        try:
            if locator.count():
                locator.last.scroll_into_view_if_needed()
                locator.last.click()
                return True
        except Exception:
            continue
    return False


def _visible_text(page) -> str:
    try:
        return page.inner_text("body", timeout=5000)
    except Exception:
        return ""


def _challenge(page) -> bool:
    """True only when the text a person would see is a challenge page.

    Looking at raw HTML gave false alarms: ordinary pages mention "captcha" or
    "access denied" inside scripts. A real challenge page has little visible
    text and says so in it.
    """
    text = _visible_text(page)
    return len(text) < 1500 and has_access_challenge(text)


def _log(page, tag: str):
    """Print what the browser sees, so a failed run can be diagnosed from the log."""
    text = re.sub(r"\s+", " ", _visible_text(page))[:500]
    try:
        title = page.title()
    except Exception:
        title = "?"
    print(f"[gojobs] {tag}: url={page.url} title={title!r} text={text!r}", flush=True)


def _signature(page) -> tuple:
    """Job ids currently listed; used to tell when a page turn has finished."""
    try:
        items = page.evaluate(COLLECT_JS, JOB_LINK.pattern)
    except Exception:
        return ()
    return tuple(job_id_from_url(urllib.parse.urljoin(BASE, i.get("href", ""))) or i.get("href", "") for i in items)


def _wait_for_results(page) -> None:
    """After Search the page shows 'Loading' for a while; wait until it is gone."""
    deadline = time.time() + RESULTS_WAIT_SECONDS
    while time.time() < deadline:
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        text = _visible_text(page)
        if "Loading" not in text[:200] and _signature(page):
            return
        time.sleep(2)


def _log_links(page) -> None:
    """Diagnostics: which links exist, so the job-link pattern can be corrected."""
    try:
        links = page.evaluate("""() => [...document.querySelectorAll('a[href]')].map(a => (a.getAttribute('href')||'').slice(0,90) + ' | ' + (a.innerText||'').trim().slice(0,40))""")
    except Exception:
        return
    print(f"[gojobs] {len(links)} links; sample: {links[:12]} ... {links[-12:]}", flush=True)


def _next_page(page, current: int) -> bool:
    """Go to results page current+1 and wait for the listing to change.

    WebForms pagers render numbered links (1 2 3 ... ), a "..." link to the next
    block of numbers, and sometimes Next/Last. Each click is a postback, so the
    page is "done" only when the list of job ids differs from before.
    """
    before = _signature(page)
    wanted = str(current + 1)
    candidates = [
        page.locator("a", has_text=re.compile(rf"^\s*{wanted}\s*$")),      # numbered link
        page.locator("a[href*='Page$" + wanted + "']"),                        # __doPostBack('...','Page$N')
        page.get_by_role("link", name=re.compile(r"^\s*(next|>|›|»|next page)\s*$", re.I)),
        page.locator("a", has_text=re.compile(r"^\s*\.\.\.\s*$")).last,      # next block of page numbers
        page.locator("input[type=submit][value*='Next' i], input[type=image][alt*='Next' i]"),
    ]
    for link in candidates:
        try:
            if not link.count():
                continue
            link.first.scroll_into_view_if_needed()
            link.first.click()
        except Exception:
            continue
        deadline = time.time() + 20
        while time.time() < deadline:
            try:
                page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                pass
            if _signature(page) not in (before, ()):
                return True
            time.sleep(0.5)
        # the click changed nothing; try the next kind of control
    return False


def collect(playwright_factory=None):
    """Collect GOjobs postings. Never raises; returns (jobs, status dict)."""
    key, label, level, region, url, _ = SOURCE
    base = {"key": key, "label": label, "government": level, "region": region, "portalUrl": url}
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [], {**base, "status": "unavailable", "count": 0,
                    "error": "playwright is not installed in this environment"}
    jobs = {}
    started = time.time()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            try:
                page = browser.new_context(user_agent=USER_AGENT.replace("CanadaGovJobs/1.0", "Mozilla/5.0 CanadaGovJobs/1.0"),
                                           locale="en-CA").new_page()
                page.set_default_timeout(30000)
                page.goto(SEARCH_URL, wait_until="networkidle")
                _log(page, "search page")
                if _challenge(page):
                    _save_debug(page, "gojobs-challenge")
                    return [], {**base, "status": "blocked_or_challenge", "count": 0}
                page.evaluate(SELECT_ALL_JS, list(FILTER_IDS))
                _save_debug(page, "gojobs-form")
                if not _press_search(page):
                    return [], {**base, "status": "no_listings_parsed", "count": 0,
                                "error": "could not find the Search button"}
                _wait_for_results(page)
                _log(page, "after Search")
                _log_links(page)
                for number in range(1, MAX_PAGES + 1):
                    if _challenge(page):
                        _save_debug(page, "gojobs-challenge")
                        status = "blocked_or_challenge"
                        return list(jobs.values()), {**base, "status": status if not jobs else "ok", "count": len(jobs)}
                    items = page.evaluate(COLLECT_JS, JOB_LINK.pattern)
                    fresh = [j for j in parse_rows(items) if j["id"] not in jobs]
                    if number == 1:
                        _save_debug(page, "gojobs-results")
                    if not fresh:
                        break
                    for job in fresh:
                        jobs[job["id"]] = job
                    print(f"[gojobs] page {number}: {len(fresh)} new, {len(jobs)} total", flush=True)
                    if (len(jobs) >= MAX_JOBS_PER_SOURCE or time.time() - started > TIME_BUDGET_SECONDS
                            or not _next_page(page, number)):
                        break
                    time.sleep(PAUSE_SECONDS)
            finally:
                browser.close()
    except Exception as error:
        return list(jobs.values()), {**base, "status": "ok" if jobs else "parse_error",
                                      "count": len(jobs), "error": str(error)[:240]}
    result = list(jobs.values())[:MAX_JOBS_PER_SOURCE]
    if result:
        return result, {**base, "status": "ok", "count": len(result)}
    return [], {**base, "status": "no_listings_parsed", "count": 0}
