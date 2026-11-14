# GCJobFinder

Government Careers Canada is a responsive, static job-discovery portal for exploring
representative federal, provincial, and territorial government job opportunities
across Canada.

## Run locally

Open `index.html` in a browser, or serve this directory with any static file server.

## Live site

https://febindonz.github.io/GCJobFinder/

GitHub Actions refreshes the public job feed daily at 07:00 UTC and deploys the
updated site. The updater checks the configured federal, provincial, and
territorial career portals, and records the source status in its workflow log.
Recent successful runs have collected listings from GC Jobs, BC, Alberta,
Saskatchewan, Manitoba, Québec, New Brunswick, Nova Scotia, and the Northwest
Territories. Other configured portals are still checked, but may block automated
access or not expose a public listing feed; source availability can also vary.
Where a portal exposes a stable posting URL, job cards open that specific
posting. If a portal only exposes a search/listing page or blocks automated
access, its status is reported and the card links to the official listings page
instead. The site uses the existing examples only if no live feed is available.

Search, government-level and region filters, sorting, region shortcuts, and
saved jobs work in the browser. Saved jobs use browser local storage.