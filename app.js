"use strict";
(() => {
  const DAY = 86400000;
  const PAGE = 30;
  const REGIONS = [
    ["BC", "British Columbia"], ["AB", "Alberta"], ["SK", "Saskatchewan"], ["MB", "Manitoba"],
    ["ON", "Ontario"], ["QC", "Quebec"], ["NB", "New Brunswick"], ["NS", "Nova Scotia"],
    ["PE", "Prince Edward Island"], ["NL", "Newfoundland and Labrador"], ["YT", "Yukon"],
    ["NT", "Northwest Territories"], ["NU", "Nunavut"], ["CA", "Canada"],
  ];
  const NAME_BY_CODE = Object.fromEntries(REGIONS);
  const FLAG = { BC: "british-columbia", AB: "alberta", SK: "saskatchewan", MB: "manitoba", ON: "ontario",
    QC: "quebec", NB: "new-brunswick", NS: "nova-scotia", PE: "prince-edward-island",
    NL: "newfoundland-and-labrador", YT: "yukon", NT: "northwest-territories", NU: "nunavut", CA: "canada" };
  const flagSrc = (name) => `assets/flags/${name}.svg`;
  const LEVELS = ["Federal", "Provincial", "Territorial"];
  const SORTS = ["new", "closing", "title", "employer"];
  const DEFAULTS = { q: "", level: "", region: "", employer: "", sort: "new",
    fresh: false, closing: false, student: false, direct: false, saved: false };
  const STATUS_TEXT = {
    ok: ["Working", "st-ok"],
    link_only: ["Link only (portal blocks automated access)", ""],
    blocked_or_challenge: ["Blocked by the portal", "st-bad"],
    no_listings_parsed: ["Reached, but no postings could be read", "st-bad"],
    unavailable: ["Could not be reached", "st-bad"],
    parse_error: ["Reader error", "st-bad"],
    robots_disallowed: ["Skipped (robots.txt)", ""],
    not_run: ["Waiting for the first refresh", ""],
  };
  const PORTALS = [
    ["Job Bank, Government of Canada", "https://www.jobbank.gc.ca/"],
    ["Job Bank open data, monthly postings (Open Government Licence)", "https://open.canada.ca/data/en/dataset/ea639e28-c0fc-48bf-b5dd-b8899bd43072"],
    ["GC Jobs open data, advertisements to the public service", "https://open.canada.ca/data/en/dataset/e61c8587-2cc9-4775-b34e-f1041ad00410"],
  ];

  const state = { ...DEFAULTS };
  let jobs = [];
  let sources = [];
  let shown = PAGE;
  let saved = loadSaved();

  const $ = (selector) => document.querySelector(selector);

  /* Build DOM with textContent only: scraped text is never parsed as HTML. */
  function el(tag, attrs, ...kids) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs || {})) {
      if (value == null || value === false) continue;
      if (key === "class") node.className = value;
      else if (key === "text") node.textContent = value;
      else if (key.startsWith("on")) node.addEventListener(key.slice(2), value);
      else node.setAttribute(key, value === true ? "" : value);
    }
    for (const kid of kids.flat()) if (kid != null && kid !== false) node.append(kid);
    return node;
  }

  function loadSaved() {
    try { return new Set(JSON.parse(localStorage.getItem("cgj.saved") || "[]")); }
    catch { return new Set(); }
  }
  function persistSaved() {
    try { localStorage.setItem("cgj.saved", JSON.stringify([...saved])); } catch { /* storage blocked */ }
  }

  const startOfToday = () => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; };
  const parseDay = (s) => (s ? new Date(`${s}T00:00:00`) : null);
  const fmtDay = (s) => { const d = parseDay(s); return d ? d.toLocaleDateString("en-CA", { month: "short", day: "numeric", year: "numeric" }) : ""; };
  const plural = (n, word) => `${n.toLocaleString()} ${word}${n === 1 ? "" : "s"}`;
  const safeUrl = (u) => { try { const p = new URL(u); return /^https?:$/.test(p.protocol) ? p.href : "#"; } catch { return "#"; } };
  const regionCode = (name) => (REGIONS.find(([, n]) => n === name) || [""])[0];

  function prepare(job) {
    const today = startOfToday();
    const when = parseDay(job.posted || job.firstSeen);
    const close = parseDay(job.closing);
    job._text = [job.title, job.employer, job.location, job.region, job.description].join(" ").toLowerCase();
    job._new = !!when && (today - when) / DAY <= 3;
    job._closeIn = close ? Math.round((close - today) / DAY) : null;
    job._sort = job.posted || job.firstSeen || "";
    job._code = regionCode(job.region);
    return job;
  }

  /* `skip` lets a facet count ignore its own filter. */
  function passes(job, skip) {
    if (state.q) {
      const text = job._text;
      for (const term of state.q.toLowerCase().split(/\s+/).filter(Boolean)) if (!text.includes(term)) return false;
    }
    if (skip !== "level" && state.level && job.government !== state.level) return false;
    if (skip !== "region" && state.region && job._code !== state.region) return false;
    if (skip !== "employer" && state.employer && job.employer !== state.employer) return false;
    if (state.fresh && !job._new) return false;
    if (state.closing && !(job._closeIn !== null && job._closeIn >= 0 && job._closeIn <= 7)) return false;
    if (state.student && !job.student) return false;
    if (state.direct && !job.direct) return false;
    if (state.saved && !saved.has(job.id)) return false;
    return true;
  }

  function sorted(list) {
    const copy = [...list];
    const by = {
      new: (a, b) => b._sort.localeCompare(a._sort),
      closing: (a, b) => (a._closeIn ?? 1e9) - (b._closeIn ?? 1e9),
      title: (a, b) => a.title.localeCompare(b.title),
      employer: (a, b) => a.employer.localeCompare(b.employer) || a.title.localeCompare(b.title),
    };
    return copy.sort(by[state.sort] || by.new);
  }

  /* URL hash keeps filters shareable. */
  function writeHash() {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(state)) {
      if (value !== DEFAULTS[key]) params.set(key, value === true ? "1" : value);
    }
    const hash = params.toString();
    history.replaceState(null, "", hash ? `#${hash}` : location.pathname + location.search);
  }
  function readHash() {
    const params = new URLSearchParams(location.hash.slice(1));
    for (const key of Object.keys(DEFAULTS)) {
      const raw = params.get(key);
      state[key] = raw == null ? DEFAULTS[key] : typeof DEFAULTS[key] === "boolean" ? raw === "1" : raw;
    }
    if (state.level && !LEVELS.includes(state.level)) state.level = "";
    if (state.region && !NAME_BY_CODE[state.region]) state.region = "";
    if (!SORTS.includes(state.sort)) state.sort = "new";
  }
  function syncControls() {
    $("#q").value = state.q;
    $("#sort").value = state.sort;
    for (const radio of document.querySelectorAll('input[name="level"]')) radio.checked = radio.value === state.level;
    for (const id of ["fresh", "closing", "student", "direct", "saved"]) $(`#${id}`).checked = state[id];
  }

  const SVG_NS = "http://www.w3.org/2000/svg";
  const FLAG_W = 33, FLAG_H = 22; // 25% smaller than the first tile version
  const CROP_TOP = 40;            // trims the far-north tip of the Arctic islands
  function svg(tag, attrs, ...kids) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [key, value] of Object.entries(attrs || {})) node.setAttribute(key, value);
    for (const kid of kids) if (kid) node.append(kid);
    return node;
  }

  function renderRegions() {
    const counts = {};
    for (const job of jobs) if (passes(job, "region")) counts[job._code] = (counts[job._code] || 0) + 1;
    const total = Object.values(counts).reduce((a, b) => a + b, 0);
    const box = $("#regions");
    box.replaceChildren();
    const toggle = (code) => { state.region = state.region === code ? "" : code; shown = PAGE; render(); };

    const map = window.CANADA_MAP;
    if (map) {
      const groups = map.provinces.map((p) => {
        const n = counts[p.code] || 0;
        const name = NAME_BY_CODE[p.code];
        const group = svg("g", {
          class: `prov${n === 0 ? " zero" : ""}`, role: "button", tabindex: "0",
          "aria-pressed": String(state.region === p.code), "aria-label": `${name}, ${plural(n, "posting")}`,
        },
          svg("title", {}),
          svg("path", { d: p.d }),
          p.leader ? svg("line", { class: "leader", x1: p.fx, y1: p.fy, x2: p.leader[0], y2: p.leader[1] }) : null,
          svg("rect", { class: "flag-edge", x: p.fx - FLAG_W / 2, y: p.fy - FLAG_H / 2, width: FLAG_W, height: FLAG_H, rx: 2 }),
          svg("image", { href: flagSrc(FLAG[p.code]), x: p.fx - FLAG_W / 2, y: p.fy - FLAG_H / 2,
            width: FLAG_W, height: FLAG_H, preserveAspectRatio: "none" }));
        group.querySelector("title").textContent = `${name} (${n.toLocaleString()})`;
        group.addEventListener("click", () => toggle(p.code));
        group.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") { event.preventDefault(); toggle(p.code); }
        });
        return group;
      });
      box.append(svg("svg", { class: "map", viewBox: `0 ${CROP_TOP} ${map.w} ${map.h - CROP_TOP}`, role: "group",
        "aria-label": "Map of Canada: choose a province or territory" }, ...groups));
    }

    const action = (code, label, n) => el("button", {
      type: "button", class: "map-btn", "aria-pressed": String(state.region === code),
      "aria-label": `${label}, ${plural(n, "posting")}`,
      onclick: () => (code === "" ? (state.region = "", shown = PAGE, render()) : toggle(code)),
    }, el("img", { src: flagSrc("canada"), alt: "", width: "26", height: "17" }), `${label} `, el("span", { class: "map-btn-n", text: n.toLocaleString() }));
    box.append(el("div", { class: "map-actions" }, action("", "All Canada", total), action("CA", "Canada-wide", counts.CA || 0)));
  }

  function renderEmployers() {
    const counts = new Map();
    for (const job of jobs) if (passes(job, "employer")) counts.set(job.employer, (counts.get(job.employer) || 0) + 1);
    const names = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0])).slice(0, 300);
    const select = $("#employer");
    select.replaceChildren(el("option", { value: "", text: "All employers" }));
    if (state.employer && !counts.has(state.employer)) select.append(el("option", { value: state.employer, text: state.employer }));
    for (const [name, n] of names) select.append(el("option", { value: name, text: `${name} (${n})` }));
    select.value = state.employer;
  }

  function card(job) {
    const tags = [];
    if (job._new) tags.push(el("span", { class: "tag tag-new", text: "New" }));
    if (job._closeIn !== null && job._closeIn >= 0 && job._closeIn <= 7) {
      tags.push(el("span", { class: "tag tag-soon", text: job._closeIn === 0 ? "Closes today" : `Closes in ${plural(job._closeIn, "day")}` }));
    }
    if (!job.direct) tags.push(el("span", { class: "tag", title: "This link opens the portal's listing page, not this exact posting.", text: "Portal listing" }));

    const facts = [];
    if (job.location) facts.push(el("li", { text: job.location }));
    if (job.salary) facts.push(el("li", { text: job.salary }));
    if (job.posted) facts.push(el("li", { text: `Posted ${fmtDay(job.posted)}` }));
    else if (job.firstSeen) facts.push(el("li", { text: `First seen ${fmtDay(job.firstSeen)}` }));
    if (job.closing) facts.push(el("li", { text: `Closes ${fmtDay(job.closing)}` }));
    facts.push(el("li", { text: `via ${job.sourceLabel}` }));

    const isSaved = saved.has(job.id);
    const save = el("button", {
      type: "button", class: "save", "aria-pressed": String(isSaved),
      "aria-label": `${isSaved ? "Remove from saved" : "Save"}: ${job.title}`, text: isSaved ? "Saved" : "Save",
      onclick: (event) => toggleSave(job, event.currentTarget),
    });
    const flag = job.government === "Federal" ? "canada" : (FLAG[job._code] || "canada");
    return el("li", { class: `job lvl-${job.government.toLowerCase()}` },
      el("img", { class: "flag", src: flagSrc(flag), alt: "", width: "46", height: "31", loading: "lazy" }),
      el("div", {},
        el("h3", {}, el("a", { href: safeUrl(job.url), target: "_blank", rel: "noopener noreferrer", text: job.title })),
        el("p", { class: "employer" }, job.employer, el("span", { class: "lvl-pill", text: job.government })),
        el("ul", { class: "facts" }, facts)),
      el("div", { class: "side" }, el("div", { class: "tags" }, tags), save));
  }

  function toggleSave(job, button) {
    if (saved.has(job.id)) saved.delete(job.id); else saved.add(job.id);
    persistSaved();
    updateSavedCount();
    if (state.saved) { render(); return; }
    const now = saved.has(job.id);
    button.setAttribute("aria-pressed", String(now));
    button.setAttribute("aria-label", `${now ? "Remove from saved" : "Save"}: ${job.title}`);
    button.textContent = now ? "Saved" : "Save";
  }
  function updateSavedCount() { $("#savedCount").textContent = saved.size ? `(${saved.size})` : ""; }

  function renderList() {
    const list = sorted(jobs.filter((job) => passes(job)));
    $("#count").textContent = `${plural(list.length, "posting")}${state.region ? ` in ${state.region === "CA" ? "Canada-wide" : NAME_BY_CODE[state.region]}` : ""}`;
    const ul = $("#list");
    ul.replaceChildren(...list.slice(0, shown).map(card));
    const empty = $("#empty");
    empty.hidden = list.length > 0;
    if (!list.length) {
      empty.replaceChildren(
        el("span", { text: state.saved ? "You have not saved any postings that match. " : "No postings match these filters. " }),
        el("button", { type: "button", class: "ghost", text: "Clear filters", onclick: clearFilters }));
      if (state.region === "ON" && !jobs.some((j) => j._code === "ON")) {
        empty.append(el("p", {},
          "Ontario postings load from Job Bank on the next scheduled refresh. Until then, browse ",
          el("a", { href: "https://www.gojobs.gov.on.ca/", target: "_blank", rel: "noopener noreferrer", text: "GOjobs, the official Ontario portal" }),
          "."));
      }
    }
    const more = $("#more");
    more.hidden = list.length <= shown;
    more.textContent = `Show ${Math.min(PAGE, list.length - shown)} more of ${(list.length - shown).toLocaleString()} remaining`;
  }

  function render() { writeHash(); syncControls(); renderRegions(); renderEmployers(); renderList(); }

  function clearFilters() { Object.assign(state, DEFAULTS); shown = PAGE; render(); }

  function renderSources(generated) {
    const body = $("#sourceTable tbody");
    body.replaceChildren(...sources.map((s) => {
      const [text, cls] = STATUS_TEXT[s.status] || [s.status, ""];
      const extra = s.carried ? ` Showing ${plural(s.carried, "earlier posting")}.` : "";
      return el("tr", {},
        el("td", {}, el("span", { class: "src-name" },
          el("img", { src: flagSrc(s.government === "Federal" ? "canada" : (FLAG[regionCode(s.region)] || "canada")), alt: "", width: "26", height: "17", loading: "lazy" }),
          s.portalUrl ? el("a", { href: safeUrl(s.portalUrl), target: "_blank", rel: "noopener noreferrer", text: s.label }) : s.label)),
        el("td", { text: s.region === "Canada" ? "Canada-wide" : s.region }),
        el("td", { class: cls, text: text + extra }),
        el("td", { class: "num", text: s.count ? s.count.toLocaleString() : "0" }),
        el("td", { text: s.lastOk ? fmtDay(s.lastOk) : "Never" }));
    }));
    $("#portals").replaceChildren(...PORTALS.map(([label, url]) =>
      el("li", {}, el("a", { href: url, target: "_blank", rel: "noopener noreferrer", text: label }))));
  }

  function renderHeader(generated) {
    const working = sources.filter((s) => s.status === "ok").length;
    const places = new Set(jobs.map((j) => j.region)).size;
    $("#lede").textContent = `${plural(jobs.length, "open posting")} from ${plural(working, "source")}, across ${plural(places, "region")}.`;
    const fresh = $("#freshness");
    if (generated) {
      const hours = (Date.now() - generated.getTime()) / 3600000;
      const when = generated.toLocaleString("en-CA", { dateStyle: "medium", timeStyle: "short" }).replace(/\.$/, "");
      fresh.textContent = `Last refreshed ${when}.` +
        (hours > 36 ? " The scheduled refresh has not run in over a day, so some postings may have closed." : "");
      fresh.classList.toggle("warn", hours > 36);
    }
  }

  function bind() {
    const on = (id, event, fn) => $(id).addEventListener(event, fn);
    on("#q", "input", (e) => { state.q = e.target.value.trim(); shown = PAGE; render(); });
    on("#sort", "change", (e) => { state.sort = e.target.value; render(); });
    on("#employer", "change", (e) => { state.employer = e.target.value; shown = PAGE; render(); });
    for (const radio of document.querySelectorAll('input[name="level"]')) {
      radio.addEventListener("change", () => { state.level = radio.value; shown = PAGE; render(); });
    }
    for (const id of ["fresh", "closing", "student", "direct", "saved"]) {
      on(`#${id}`, "change", (e) => { state[id] = e.target.checked; shown = PAGE; render(); });
    }
    on("#clear", "click", clearFilters);
    on("#more", "click", () => { shown += PAGE; renderList(); });
    window.addEventListener("hashchange", () => { readHash(); shown = PAGE; render(); });
    if (window.matchMedia("(max-width: 820px)").matches) $("#filters").removeAttribute("open");
  }

  async function start() {
    bind();
    updateSavedCount();
    try {
      const response = await fetch("data/jobs.json", { cache: "no-cache" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      jobs = (data.jobs || []).filter((j) => j && j.title && j.url).map(prepare);
      sources = data.sources || [];
      readHash();
      renderHeader(data.generatedAt ? new Date(data.generatedAt) : null);
      renderSources();
      render();
    } catch (error) {
      $("#lede").textContent = "The postings file could not be loaded. Reload the page, or open the official portals listed below.";
      renderSources();
    }
  }
  start();
})();
