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
The home-page portal panel links directly to the official federal, provincial,
and territorial career sites. It uses public-domain jurisdiction flag artwork
from [Wikimedia Commons](https://commons.wikimedia.org/wiki/Category:Flags_of_provinces_and_territories_of_Canada)
for identification; these are flags, not government wordmark logos. An empty
regional feed is not evidence that the official portal has no vacancies.
The Ontario search page currently returns a form rather than job-result records
to the updater, so Ontario openings are not included in the feed; selecting an
unavailable region offers a direct link to its official careers portal.

Search, government-level and region filters, sorting, region shortcuts, and
saved jobs work in the browser. Saved jobs use browser local storage.