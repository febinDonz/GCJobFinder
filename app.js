const jobs = [
  {
    id: "climate-policy",
    title: "Policy Analyst, Climate Adaptation",
    agency: "Environment and Climate Change Canada",
    departmentShort: "ECCC",
    mark: "E",
    color: "green",
    location: "Ottawa, ON · Hybrid",
    type: "Full-time",
    level: "EC-04",
    salaryText: "$82,430 – $94,340",
    posted: "2026-11-12",
    postedText: "Posted 1 day ago",
    arrangement: "Hybrid",
    student: false,
    description: "Help shape evidence-based climate adaptation policy with a collaborative team working to protect communities across Canada."
  },
  {
    id: "parks-interpreter",
    title: "Visitor Experience Officer",
    agency: "Parks Canada",
    departmentShort: "Parks Canada",
    mark: "P",
    color: "green",
    location: "Banff, AB · On-site",
    type: "Full-time",
    level: "PM-02",
    salaryText: "$61,152 – $68,433",
    posted: "2026-11-10",
    postedText: "Posted 3 days ago",
    arrangement: "On-site",
    student: false,
    description: "Welcome visitors to one of Canada's most treasured places and help connect people with nature and our shared heritage."
  },
  {
    id: "cra-data",
    title: "Data Analyst, Digital Services",
    agency: "Canada Revenue Agency",
    departmentShort: "CRA",
    mark: "C",
    color: "blue",
    location: "Toronto, ON · Remote eligible",
    type: "Full-time",
    level: "IT-02",
    salaryText: "$75,129 – $88,833",
    posted: "2026-11-08",
    postedText: "Posted 5 days ago",
    arrangement: "Remote",
    student: false,
    description: "Turn complex data into clear insights that make digital tax services simpler and more accessible for Canadians."
  },
  {
    id: "esdc-student",
    title: "Junior Program Officer — Student",
    agency: "Employment and Social Development Canada",
    departmentShort: "ESDC",
    mark: "S",
    color: "purple",
    location: "Montréal, QC · Hybrid",
    type: "Student",
    level: "Student",
    salaryText: "$22.71 – $29.37 per hour",
    posted: "2026-11-07",
    postedText: "Posted 6 days ago",
    arrangement: "Hybrid",
    student: true,
    description: "Build hands-on experience supporting programs that help people access skills training, employment services, and benefits."
  },
  {
    id: "public-safety",
    title: "Emergency Management Specialist",
    agency: "Public Safety Canada",
    departmentShort: "PSC",
    mark: "S",
    color: "gold",
    location: "Ottawa, ON · Hybrid",
    type: "Full-time",
    level: "PM-04",
    salaryText: "$82,430 – $94,340",
    posted: "2026-11-05",
    postedText: "Posted 8 days ago",
    arrangement: "Hybrid",
    student: false,
    description: "Work with partners across the country to strengthen Canada's preparedness for emergencies and support resilient communities."
  },
  {
    id: "health-research",
    title: "Research Coordinator, Public Health",
    agency: "Public Health Agency of Canada",
    departmentShort: "PHAC",
    mark: "H",
    color: "teal",
    location: "Winnipeg, MB · Remote eligible",
    type: "Full-time",
    level: "BI-03",
    salaryText: "$74,023 – $100,285",
    posted: "2026-11-03",
    postedText: "Posted 10 days ago",
    arrangement: "Remote",
    student: false,
    description: "Coordinate collaborative research projects that support better health outcomes for people and communities nationwide."
  },
  {
    id: "parks-student",
    title: "Ecology Field Assistant — Student",
    agency: "Parks Canada",
    departmentShort: "Parks Canada",
    mark: "P",
    color: "green",
    location: "Jasper, AB · On-site",
    type: "Student",
    level: "Student",
    salaryText: "$20.56 – $26.57 per hour",
    posted: "2026-10-30",
    postedText: "Posted 14 days ago",
    arrangement: "On-site",
    student: true,
    description: "Join a field team monitoring wildlife and ecosystems while gaining practical conservation experience in a national park."
  },
  {
    id: "digital-service",
    title: "UX Designer, Digital Services",
    agency: "Shared Services Canada",
    departmentShort: "SSC",
    mark: "D",
    color: "blue",
    location: "Canada-wide · Remote",
    type: "Full-time",
    level: "CS-03",
    salaryText: "$87,184 – $105,242",
    posted: "2026-10-28",
    postedText: "Posted 16 days ago",
    arrangement: "Remote",
    student: false,
    description: "Design accessible, human-centred digital experiences for services used by people across Canada."
  },
  {
    id: "bc-program-analyst",
    title: "Program Analyst, Public Services",
    agency: "BC Public Service",
    mark: "BC",
    color: "blue",
    government: "Provincial",
    region: "British Columbia",
    location: "Victoria, BC",
    type: "Full-time",
    level: "Public service",
    salaryText: "See official posting",
    posted: "2026-11-12",
    postedText: "Representative example",
    arrangement: "On-site",
    student: false,
    sourceLabel: "BC Public Service",
    sourceUrl: "https://bcpublicservice.hua.hrsmart.com/hr/ats/JobSearch/viewAll",
    description: "Support programs and services that strengthen communities throughout British Columbia."
  },
  {
    id: "alberta-data-analyst",
    title: "Data Analyst, Public Programs",
    agency: "Alberta Public Service",
    mark: "AB",
    color: "blue",
    government: "Provincial",
    region: "Alberta",
    location: "Edmonton, AB",
    type: "Full-time",
    level: "Public service",
    salaryText: "See official posting",
    posted: "2026-11-11",
    postedText: "Representative example",
    arrangement: "Hybrid",
    student: false,
    sourceLabel: "Alberta Public Service",
    sourceUrl: "https://jobpostings.alberta.ca/",
    description: "Use research and data to help improve public programs and services for Albertans."
  },
  {
    id: "saskatchewan-policy-officer",
    title: "Policy Officer, Community Programs",
    agency: "Government of Saskatchewan",
    mark: "SK",
    color: "blue",
    government: "Provincial",
    region: "Saskatchewan",
    location: "Regina, SK",
    type: "Full-time",
    level: "Public service",
    salaryText: "See official posting",
    posted: "2026-11-10",
    postedText: "Representative example",
    arrangement: "Hybrid",
    student: false,
    sourceLabel: "Saskatchewan Public Service",
    sourceUrl: "https://careers.saskatchewan.ca/",
    description: "Help develop and deliver policies that support Saskatchewan communities and families."
  },
  {
    id: "manitoba-program-officer",
    title: "Program Officer, Public Services",
    agency: "Manitoba Government",
    mark: "MB",
    color: "blue",
    government: "Provincial",
    region: "Manitoba",
    location: "Winnipeg, MB",
    type: "Full-time",
    level: "Public service",
    salaryText: "See official posting",
    posted: "2026-11-09",
    postedText: "Representative example",
    arrangement: "Hybrid",
    student: false,
    sourceLabel: "Manitoba Government",
    sourceUrl: "https://jobsearch.gov.mb.ca/",
    description: "Coordinate public programs that help Manitobans access the services they need."
  },
  {
    id: "ontario-policy-advisor",
    title: "Policy Advisor, Community Services",
    agency: "Ontario Public Service",
    mark: "ON",
    color: "blue",
    government: "Provincial",
    region: "Ontario",
    location: "Toronto, ON",
    type: "Full-time",
    level: "Public service",
    salaryText: "See official posting",
    posted: "2026-11-08",
    postedText: "Representative example",
    arrangement: "Hybrid",
    student: false,
    sourceLabel: "Ontario Public Service",
    sourceUrl: "https://www.gojobs.gov.on.ca/Jobs.aspx",
    description: "Contribute policy research and advice to programs serving people across Ontario."
  },
  {
    id: "quebec-policy-analyst",
    title: "Policy Analyst, Public Programs",
    agency: "Québec Public Service",
    mark: "QC",
    color: "blue",
    government: "Provincial",
    region: "Quebec",
    location: "Montréal, QC",
    type: "Full-time",
    level: "Public service",
    salaryText: "See official posting",
    posted: "2026-11-07",
    postedText: "Representative example",
    arrangement: "Hybrid",
    student: false,
    sourceLabel: "Québec Government",
    sourceUrl: "https://recrutement.carrieres.gouv.qc.ca/",
    description: "Research public policy options and support programs that benefit people throughout Québec."
  },
  {
    id: "new-brunswick-program-consultant",
    title: "Program Consultant, Social Development",
    agency: "Government of New Brunswick",
    mark: "NB",
    color: "blue",
    government: "Provincial",
    region: "New Brunswick",
    location: "Fredericton, NB",
    type: "Full-time",
    level: "Public service",
    salaryText: "See official posting",
    posted: "2026-11-06",
    postedText: "Representative example",
    arrangement: "Hybrid",
    student: false,
    sourceLabel: "New Brunswick Government",
    sourceUrl: "https://www.ere.gnb.ca/competition.aspx?culture=en-CA",
    description: "Help coordinate social programs and services for individuals and families in New Brunswick."
  },
  {
    id: "nova-scotia-emergency-management",
    title: "Emergency Management Officer",
    agency: "Government of Nova Scotia",
    mark: "NS",
    color: "blue",
    government: "Provincial",
    region: "Nova Scotia",
    location: "Halifax, NS",
    type: "Full-time",
    level: "Public service",
    salaryText: "See official posting",
    posted: "2026-11-05",
    postedText: "Representative example",
    arrangement: "Hybrid",
    student: false,
    sourceLabel: "Nova Scotia Government",
    sourceUrl: "https://jobs.novascotia.ca/",
    description: "Work with partners to prepare for emergencies and support resilient communities in Nova Scotia."
  },
  {
    id: "pei-policy-analyst",
    title: "Policy Analyst, Public Programs",
    agency: "Government of Prince Edward Island",
    mark: "PE",
    color: "blue",
    government: "Provincial",
    region: "Prince Edward Island",
    location: "Charlottetown, PE",
    type: "Full-time",
    level: "Public service",
    salaryText: "See official posting",
    posted: "2026-11-04",
    postedText: "Representative example",
    arrangement: "Hybrid",
    student: false,
    sourceLabel: "Prince Edward Island Government",
    sourceUrl: "https://www.princeedwardisland.ca/en/topic/employment-opportunities",
    description: "Support the development of public policies and programs for Prince Edward Island residents."
  },
  {
    id: "newfoundland-program-analyst",
    title: "Program Analyst, Public Services",
    agency: "Government of Newfoundland and Labrador",
    mark: "NL",
    color: "blue",
    government: "Provincial",
    region: "Newfoundland and Labrador",
    location: "St. John's, NL",
    type: "Full-time",
    level: "Public service",
    salaryText: "See official posting",
    posted: "2026-11-03",
    postedText: "Representative example",
    arrangement: "Hybrid",
    student: false,
    sourceLabel: "Newfoundland and Labrador Government",
    sourceUrl: "https://www.hiring.gov.nl.ca/",
    description: "Contribute to public programs and services for people in Newfoundland and Labrador."
  },
  {
    id: "yukon-conservation-officer",
    title: "Conservation Program Officer",
    agency: "Government of Yukon",
    mark: "YT",
    color: "blue",
    government: "Territorial",
    region: "Yukon",
    location: "Whitehorse, YT",
    type: "Full-time",
    level: "Territorial public service",
    salaryText: "See official posting",
    posted: "2026-11-02",
    postedText: "Representative example",
    arrangement: "On-site",
    student: false,
    sourceLabel: "Government of Yukon",
    sourceUrl: "https://yukon.ca/en/employment",
    description: "Support conservation and community programs across Yukon’s diverse landscapes."
  },
  {
    id: "nwt-community-program-officer",
    title: "Community Program Officer",
    agency: "Government of the Northwest Territories",
    mark: "NT",
    color: "blue",
    government: "Territorial",
    region: "Northwest Territories",
    location: "Yellowknife, NT",
    type: "Full-time",
    level: "Territorial public service",
    salaryText: "See official posting",
    posted: "2026-11-01",
    postedText: "Representative example",
    arrangement: "Hybrid",
    student: false,
    sourceLabel: "Government of the Northwest Territories",
    sourceUrl: "https://www.gov.nt.ca/careers/",
    description: "Work with community partners to deliver programs for residents across the Northwest Territories."
  },
  {
    id: "nunavut-health-program-officer",
    title: "Health Program Officer",
    agency: "Government of Nunavut",
    mark: "NU",
    color: "blue",
    government: "Territorial",
    region: "Nunavut",
    location: "Iqaluit, NU",
    type: "Full-time",
    level: "Territorial public service",
    salaryText: "See official posting",
    posted: "2026-10-31",
    postedText: "Representative example",
    arrangement: "On-site",
    student: false,
    sourceLabel: "Government of Nunavut",
    sourceUrl: "https://gov.nu.ca/en/careers",
    description: "Support health programs and services for communities across Nunavut."
  }
];

let feedSources = [];

async function loadLiveGovernmentJobs() {
  try {
    const response = await fetch(new URL("jobs.json", document.baseURI), { cache: "no-store" });
    if (!response.ok) throw new Error(`Job feed request failed with status ${response.status}`);
    const feed = await response.json();
    if (!Array.isArray(feed.jobs)) throw new Error("Job feed has no jobs array");

    const liveJobs = feed.jobs.filter((job) =>
      job && typeof job.id === "string" &&
      typeof job.title === "string" &&
      typeof job.sourceUrl === "string" &&
      /^https?:\/\//i.test(job.sourceUrl)
    );
    if (!liveJobs.length) return;

    jobs.splice(0, jobs.length, ...liveJobs);
    populateFilters();
    renderJobs();

    feedSources = Array.isArray(feed.sources) ? feed.sources : [];
    const unavailableSources = feedSources.filter((source) => source.status !== "ok");
    const availableSourceCount = feedSources.length - unavailableSources.length;
    document.querySelector("#listingNoticeTitle").textContent = unavailableSources.length
      ? `${availableSourceCount} of ${feedSources.length} sources reporting`
      : "Live government postings";
    document.querySelector("#listingNoticeBody").textContent = unavailableSources.length
      ? `${unavailableSources.length} portal feeds could not be collected today. Missing feed data does not mean no openings; use the portal links above.`
      : "Listings refresh daily. Confirm details and deadlines on the official posting.";
    const updated = document.querySelector("#feedUpdated");
    if (updated && feed.generatedAt) {
      const generatedAt = new Date(feed.generatedAt);
      if (!Number.isNaN(generatedAt.getTime())) {
        const sourceNote = unavailableSources.length
          ? ` ${unavailableSources.length} portal feeds were unavailable.`
          : "";
        updated.textContent = `Live postings refreshed ${generatedAt.toLocaleString(undefined, { timeZone: "UTC" })} UTC.${sourceNote} Verify details on the official posting.`;
      }
    }
    showToast("Live government postings loaded.");
  } catch (error) {
    console.warn("Live job feed could not be loaded; showing the example listings.", error);
    document.querySelector("#listingNoticeTitle").textContent = "Example listings";
    document.querySelector("#listingNoticeBody").textContent = "The live feed is unavailable. Check official listings for current vacancies.";
    const updated = document.querySelector("#feedUpdated");
    if (updated) updated.textContent = "Live feed unavailable; showing examples. Check official listings for current vacancies.";
  }
}

const officialJobsUrl = "https://emploisfp-psjobs.cfp-psc.gc.ca/psrs-srfp/applicant/page2440?fromMenu=true";
const regions = [
  "Alberta",
  "British Columbia",
  "Manitoba",
  "New Brunswick",
  "Newfoundland and Labrador",
  "Northwest Territories",
  "Nova Scotia",
  "Nunavut",
  "Ontario",
  "Prince Edward Island",
  "Quebec",
  "Saskatchewan",
  "Yukon"
];
const regionByCode = {
  AB: "Alberta",
  BC: "British Columbia",
  MB: "Manitoba",
  NB: "New Brunswick",
  NL: "Newfoundland and Labrador",
  NT: "Northwest Territories",
  NS: "Nova Scotia",
  NU: "Nunavut",
  ON: "Ontario",
  PE: "Prince Edward Island",
  QC: "Quebec",
  SK: "Saskatchewan",
  YT: "Yukon"
};
for (const job of jobs) {
  job.government ||= "Federal";
  job.sourceLabel ||= "GC Jobs";
  job.sourceUrl ||= officialJobsUrl;
  job.directPosting ??= false;
  const provinceCode = job.location.match(/\b(AB|BC|MB|NB|NL|NT|NS|NU|ON|PE|QC|SK|YT)\b/)?.[0];
  job.region ||= provinceCode ? regionByCode[provinceCode] : "";
}
const elements = {
  keyword: document.querySelector("#keywordInput"),
  location: document.querySelector("#locationInput"),
  agency: document.querySelector("#agencyFilter"),
  government: document.querySelector("#governmentFilter"),
  region: document.querySelector("#regionFilter"),
  type: document.querySelector("#typeFilter"),
  remote: document.querySelector("#remoteFilter"),
  student: document.querySelector("#studentFilter"),
  sort: document.querySelector("#sortFilter"),
  list: document.querySelector("#jobList"),
  summary: document.querySelector("#resultsSummary"),
  empty: document.querySelector("#emptyState"),
  savedCount: document.querySelector("#savedCount"),
  toast: document.querySelector("#toast")
};
const savedJobsKey = "gc-careers-saved-jobs";
let savedJobs = readSavedJobs();
let savedOnly = false;
let toastTimer;

function readSavedJobs() {
  try {
    const stored = JSON.parse(localStorage.getItem(savedJobsKey) || "[]");
    return new Set(Array.isArray(stored) ? stored.filter((id) => typeof id === "string") : []);
  } catch (error) {
    console.warn("Saved jobs could not be loaded from this browser.", error);
    return new Set();
  }
}

function saveSavedJobs() {
  try {
    localStorage.setItem(savedJobsKey, JSON.stringify([...savedJobs]));
  } catch (error) {
    console.warn("Saved jobs could not be stored in this browser.", error);
    showToast("Your browser couldn't save this job. Try again later.");
  }
}

function populateFilters() {
  const agencies = [...new Set(jobs.map((job) => job.agency))].sort();
  const types = [...new Set(jobs.map((job) => job.type))].sort();

  elements.agency.innerHTML = '<option value="">All departments & employers</option>';
  elements.type.innerHTML = '<option value="">All types</option>';
  elements.region.innerHTML = '<option value="">All provinces & territories</option>';

  for (const agency of agencies) {
    elements.agency.add(new Option(agency, agency));
  }
  for (const type of types) {
    elements.type.add(new Option(type, type));
  }
  for (const region of regions) {
    elements.region.add(new Option(region, region));
  }
}

function matchesSearch(job, query) {
  if (!query) return true;
  const searchable = [job.title, job.agency, job.government, job.region, job.level, job.description, job.type, job.arrangement].join(" ").toLowerCase();
  return searchable.includes(query);
}

function getVisibleJobs() {
  const query = elements.keyword.value.trim().toLowerCase();
  const locationQuery = elements.location.value.trim().toLowerCase();
  const filtered = jobs.filter((job) => {
    const matchesLocation = !locationQuery || job.location.toLowerCase().includes(locationQuery) ||
      job.region.toLowerCase().includes(locationQuery) ||
      (locationQuery === "remote" && job.arrangement === "Remote");
    return matchesSearch(job, query) &&
      matchesLocation &&
      (!elements.agency.value || job.agency === elements.agency.value) &&
      (!elements.government.value || job.government === elements.government.value) &&
      (!elements.region.value || job.region === elements.region.value) &&
      (!elements.type.value || job.type === elements.type.value) &&
      (!elements.remote.checked || job.arrangement === "Remote" || job.arrangement === "Hybrid") &&
      (!elements.student.checked || job.student) &&
      (!savedOnly || savedJobs.has(job.id));
  });

  if (elements.sort.value === "title") filtered.sort((a, b) => a.title.localeCompare(b.title));
  if (elements.sort.value === "department") filtered.sort((a, b) => a.agency.localeCompare(b.agency) || a.title.localeCompare(b.title));
  if (elements.sort.value === "recent") filtered.sort((a, b) => b.posted.localeCompare(a.posted));
  return filtered;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  })[character]);
}

function renderJobs() {
  const visibleJobs = getVisibleJobs();
  elements.list.innerHTML = visibleJobs.map((job) => {
    const isSaved = savedJobs.has(job.id);
    const title = escapeHtml(job.title);
    const agency = escapeHtml(job.agency);
    const mark = escapeHtml(job.mark || job.agency.slice(0, 2).toUpperCase());
    const color = escapeHtml(job.color || "blue");
    const sourceLabel = escapeHtml(job.sourceLabel || "official careers portal");
    const sourceUrl = escapeHtml(/^https?:\/\//i.test(job.sourceUrl) ? job.sourceUrl : officialJobsUrl);
    const postingLinkLabel = job.directPosting === false
      ? `Find listings at ${sourceLabel}`
      : `View posting at ${sourceLabel}`;
    const tags = [
      `<span class="job-tag">${escapeHtml(job.type)}</span>`,
      `<span class="job-tag government-tag">${escapeHtml(job.government)} government</span>`,
      `<span class="job-tag">${escapeHtml(job.level)}</span>`,
      `<span class="job-tag">${escapeHtml(job.arrangement)}</span>`,
      job.student ? '<span class="job-tag new">Student</span>' : ""
    ].join("");
    return `
      <article class="job-card">
        <div class="job-card-top">
          <span class="agency-mark ${color}" aria-hidden="true">${mark}</span>
          <div class="job-main">
            <h3 class="job-title">${title}</h3>
            <p class="agency-name">${agency}</p>
            <p class="job-description">${escapeHtml(job.description)}</p>
          </div>
          <button class="save-button${isSaved ? " is-saved" : ""}" type="button" data-save="${escapeHtml(job.id)}" aria-label="${isSaved ? "Remove saved job" : "Save job"}: ${title}" aria-pressed="${isSaved}">${isSaved ? "♥" : "♡"}</button>
        </div>
        <div class="job-meta">
          <span><svg class="meta-icon" aria-hidden="true" viewBox="0 0 24 24" fill="none"><path d="M19 10.1c0 5-7 11-7 11s-7-6-7-11a7 7 0 1 1 14 0Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"></path><circle cx="12" cy="10" r="2.2" stroke="currentColor" stroke-width="1.8"></circle></svg>${escapeHtml(job.location)}</span>
          <span><span class="meta-icon salary-icon" aria-hidden="true">$</span>${escapeHtml(job.salaryText)}</span>
        </div>
        <div class="job-tags">${tags}</div>
        <div class="job-card-bottom">
          <span class="posted-date">${escapeHtml(job.postedText)}</span>
          <a class="view-job" href="${sourceUrl}" target="_blank" rel="noopener noreferrer">${postingLinkLabel} <span aria-hidden="true">↗</span></a>
        </div>
      </article>`;
  }).join("");

  const count = visibleJobs.length;
  const countLabel = `${count} ${count === 1 ? "opportunity" : "opportunities"}`;
  elements.summary.innerHTML = `<strong>${countLabel}</strong> ${savedOnly ? "saved" : "across Canada"}`;
  const emptyTitle = elements.empty.querySelector("h3");
  const emptyMessage = elements.empty.querySelector("p");
  const emptySourceLink = elements.empty.querySelector("#emptySourceLink");
  const selectedPortal = Array.from(document.querySelectorAll(".portal-link[data-portal-region]"))
    .find((portal) => portal.dataset.portalRegion === elements.region.value);
  const selectedPortalSource = feedSources.find((source) => source.key === selectedPortal?.dataset.sourceKey);
  if (!count && selectedPortal && selectedPortalSource && selectedPortalSource.status !== "ok") {
    emptyTitle.textContent = `No ${elements.region.value} postings in today's feed`;
    emptyMessage.textContent = "The official portal may still have active openings; its listings were not available to today's feed.";
    emptySourceLink.href = selectedPortal.href;
    emptySourceLink.textContent = `Browse official ${elements.region.value} jobs ↗`;
    emptySourceLink.hidden = false;
  } else {
    emptyTitle.textContent = "No opportunities found";
    emptyMessage.textContent = "Try changing your search or clearing a filter to see more roles.";
    emptySourceLink.hidden = true;
    emptySourceLink.removeAttribute("href");
  }
  elements.empty.hidden = count > 0;
  elements.list.hidden = count === 0;
  elements.savedCount.textContent = String(savedJobs.size);
  document.querySelector("#savedNav").classList.toggle("saved-nav-active", savedOnly);
}

function showToast(message) {
  elements.toast.textContent = message;
  elements.toast.classList.add("visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => elements.toast.classList.remove("visible"), 2500);
}

function clearFilters() {
  elements.keyword.value = "";
  elements.location.value = "";
  elements.agency.value = "";
  elements.government.value = "";
  elements.region.value = "";
  elements.type.value = "";
  elements.remote.checked = false;
  elements.student.checked = false;
  savedOnly = false;
  renderJobs();
}

document.querySelector("#searchForm").addEventListener("submit", (event) => {
  event.preventDefault();
  savedOnly = false;
  renderJobs();
  document.querySelector("#opportunities").scrollIntoView({ behavior: "smooth", block: "start" });
});

for (const control of [elements.keyword, elements.location]) {
  control.addEventListener("input", () => {
    savedOnly = false;
    renderJobs();
  });
}
for (const control of [elements.agency, elements.government, elements.region, elements.type, elements.remote, elements.student, elements.sort]) {
  control.addEventListener("change", renderJobs);
}

document.querySelector("#clearFilters").addEventListener("click", clearFilters);
document.querySelector("#emptyClear").addEventListener("click", clearFilters);
document.querySelector("#savedNav").addEventListener("click", () => {
  savedOnly = !savedOnly;
  renderJobs();
  document.querySelector("#opportunities").scrollIntoView({ behavior: "smooth", block: "start" });
  if (savedOnly && savedJobs.size === 0) showToast("Save a job to find it here later.");
});

document.querySelector("#jobList").addEventListener("click", (event) => {
  const button = event.target.closest("[data-save]");
  if (!button) return;
  const job = jobs.find((entry) => entry.id === button.dataset.save);
  if (!job) return;
  if (savedJobs.has(job.id)) {
    savedJobs.delete(job.id);
    showToast("Removed from your saved jobs.");
  } else {
    savedJobs.add(job.id);
    showToast("Job saved for later.");
  }
  saveSavedJobs();
  renderJobs();
});

document.querySelectorAll("[data-search]").forEach((button) => {
  button.addEventListener("click", () => {
    elements.keyword.value = button.dataset.search === "remote" ? "" : button.dataset.search;
    if (button.dataset.search === "remote") {
      elements.remote.checked = true;
      elements.location.value = "";
    } else {
      elements.remote.checked = false;
    }
    if (button.dataset.search === "student") elements.student.checked = true;
    else elements.student.checked = false;
    savedOnly = false;
    renderJobs();
    document.querySelector("#opportunities").scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

document.querySelectorAll(".department-card").forEach((card) => {
  card.addEventListener("click", () => {
    elements.region.value = card.dataset.region;
    savedOnly = false;
    renderJobs();
    document.querySelector("#opportunities").scrollIntoView({ behavior: "smooth", block: "start" });
  });
});

const menuToggle = document.querySelector("#menuToggle");
const mainNav = document.querySelector("#mainNav");
menuToggle.addEventListener("click", () => {
  const isOpen = menuToggle.getAttribute("aria-expanded") === "true";
  menuToggle.setAttribute("aria-expanded", String(!isOpen));
  menuToggle.setAttribute("aria-label", isOpen ? "Open navigation" : "Close navigation");
  mainNav.classList.toggle("open", !isOpen);
});
mainNav.addEventListener("click", (event) => {
  if (event.target.closest("a")) {
    mainNav.classList.remove("open");
    menuToggle.setAttribute("aria-expanded", "false");
    menuToggle.setAttribute("aria-label", "Open navigation");
  }
});

populateFilters();
renderJobs();
loadLiveGovernmentJobs();
