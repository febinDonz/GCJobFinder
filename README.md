# Canada public sector jobs

A static website listing federal, provincial and territorial government jobs in
one searchable page. A scheduled GitHub Action collects postings twice a day
into `data/jobs.json` and redeploys the site to GitHub Pages.

## Deploy

1. Create a GitHub repository and push this folder to `main`.
2. Settings, Pages, Source: **GitHub Actions**.
3. Run the **Refresh jobs and deploy** workflow once (Actions tab, Run workflow).
4. Open the **Where the postings come from** table on the live site. It shows
   what each source actually returned on that run.

Run locally: `python3 -m http.server` and open http://localhost:8000.
Refresh data locally: `python3 -m scripts.govjobs.run`. Tests: `python3 -m unittest discover -s tests -t .`

## Sources

| Level | Source | How |
|---|---|---|
| Federal | GC Jobs | Portal listing (links to the GC Jobs search, not each poster) |
| Federal | Job Bank, by employer | Search results pages, one link per posting |
| BC, AB, SK, MB, NS, NWT | Official provincial / territorial portals | Parsers carried over from GCJobFinder, now uncapped (500 per source) |
| QC, NB, NL, PEI, YT, NU | Official portals | Best effort; several block or hide listings from bots |
| **Ontario** | Job Bank, employer "Ontario Public Service" | See below |

### Ontario

GOjobs (`gojobs.gov.on.ca`) lists nothing until its Search button is pressed,
and its filters need JavaScript. `scripts/govjobs/gojobs.py` drives a headless
browser (Playwright, installed by the workflow): open Search.aspx, tick every
option in the required filters, press Search, read the results, page through them.
It follows GOjobs' `robots.txt` (only `/alljobs.aspx` and `/ReadPDF.aspx` are
disallowed). If a CAPTCHA appears it stops and reports `blocked_or_challenge`;
it never tries to bypass one. Job Bank's Ontario Public Service postings are
collected too, and duplicates are merged with GOjobs preferred.

This was written without seeing the live page. Each run uploads a screenshot
and HTML of the form and results as the **gojobs-debug** artifact (Actions run
page, Artifacts). If the Ontario GOjobs row is not "Working", open it and fix
the selectors at the top of `gojobs.py`.

### Not used yet

- **Job Bank monthly open data CSV** (Open Government Licence, open.canada.ca):
  complete and stable, but published monthly and only covers postings Job Bank
  carries. Good for trend analysis, not a live board.
- **GC Jobs "Advertisements to the Public Service" open data**: quarterly
  updates, so it lags behind the live portal.

## How failures are handled

- Every source reports a status (`ok`, `blocked_or_challenge`, `unavailable`, ...).
- A failing source keeps its previous postings for up to 7 days and is marked on
  the page. If nothing at all is collected, `data/jobs.json` is left untouched.
- Postings past their closing date are dropped. The same posting seen through
  two sources is shown once, preferring the official portal.
- Job Bank is read politely: `robots.txt` is honoured, one request per second.

## Adding or fixing a source

- Portal with its own listing: add a tuple to `SOURCES` and a `parse_*`
  function in `scripts/govjobs/portals.py`.
- Another employer on Job Bank: add a group in `scripts/govjobs/jobbank.py`.

The Job Bank result parser was written from the structure of the result pages
and tested against a synthetic card, not a captured page. If the Ontario row
shows "Reached, but no postings could be read" after the first run, its
selectors in `parse_results` are what to adjust.
