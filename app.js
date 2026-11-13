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
  }
];

const officialJobsUrl = "https://www.canada.ca/en/services/jobs/opportunities/government.html";
const elements = {
  keyword: document.querySelector("#keywordInput"),
  location: document.querySelector("#locationInput"),
  agency: document.querySelector("#agencyFilter"),
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
  for (const agency of agencies) {
    elements.agency.add(new Option(agency, agency));
  }
  for (const type of types) {
    elements.type.add(new Option(type, type));
  }
}

function matchesSearch(job, query) {
  if (!query) return true;
  const searchable = [job.title, job.agency, job.level, job.description, job.type, job.arrangement].join(" ").toLowerCase();
  return searchable.includes(query);
}

function getVisibleJobs() {
  const query = elements.keyword.value.trim().toLowerCase();
  const locationQuery = elements.location.value.trim().toLowerCase();
  const filtered = jobs.filter((job) => {
    const matchesLocation = !locationQuery || job.location.toLowerCase().includes(locationQuery) ||
      (locationQuery === "remote" && job.arrangement === "Remote");
    return matchesSearch(job, query) &&
      matchesLocation &&
      (!elements.agency.value || job.agency === elements.agency.value) &&
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

function renderJobs() {
  const visibleJobs = getVisibleJobs();
  elements.list.innerHTML = visibleJobs.map((job) => {
    const isSaved = savedJobs.has(job.id);
    const tags = [
      `<span class="job-tag">${job.type}</span>`,
      `<span class="job-tag">${job.level}</span>`,
      `<span class="job-tag">${job.arrangement}</span>`,
      job.student ? '<span class="job-tag new">Student</span>' : ""
    ].join("");
    return `
      <article class="job-card">
        <div class="job-card-top">
          <span class="agency-mark ${job.color}" aria-hidden="true">${job.mark}</span>
          <div class="job-main">
            <h3 class="job-title">${job.title}</h3>
            <p class="agency-name">${job.agency}</p>
            <p class="job-description">${job.description}</p>
          </div>
          <button class="save-button${isSaved ? " is-saved" : ""}" type="button" data-save="${job.id}" aria-label="${isSaved ? "Remove saved job" : "Save job"}: ${job.title}" aria-pressed="${isSaved}">${isSaved ? "♥" : "♡"}</button>
        </div>
        <div class="job-meta">
          <span><span class="meta-icon" aria-hidden="true">⌖</span>${job.location}</span>
          <span><span class="meta-icon" aria-hidden="true">＄</span>${job.salaryText}</span>
        </div>
        <div class="job-tags">${tags}</div>
        <div class="job-card-bottom">
          <span class="posted-date">${job.postedText}</span>
          <a class="view-job" href="${officialJobsUrl}" target="_blank" rel="noreferrer">View on GC Jobs <span aria-hidden="true">↗</span></a>
        </div>
      </article>`;
  }).join("");

  const count = visibleJobs.length;
  const countLabel = `${count} ${count === 1 ? "opportunity" : "opportunities"}`;
  elements.summary.innerHTML = `<strong>${countLabel}</strong> ${savedOnly ? "saved" : "across Canada"}`;
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
for (const control of [elements.agency, elements.type, elements.remote, elements.student, elements.sort]) {
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
    elements.agency.value = card.dataset.agency;
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
