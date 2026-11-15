"""Refresh data/jobs.json from every configured source.

    python -m scripts.govjobs.run

Safe by design: a source that fails keeps its previous postings (up to
CARRY_DAYS old) and is flagged in the sources table, and nothing is written if
no postings at all could be collected.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from . import gojobs, jobbank, portals
from .common import TODAY

OUTPUT = Path(__file__).resolve().parents[2] / "data" / "jobs.json"
CARRY_DAYS = 7


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def dedupe(jobs: list) -> list:
    """Collapse the same posting seen through two portals. Prefer direct links
    and portal-native sources over Job Bank copies."""
    best = {}
    for job in jobs:
        key = "|".join(_norm(job.get(f, "")) for f in ("title", "employer", "location", "closing"))
        rank = (job.get("direct", False), not job["source"].startswith("jb-"))
        if key not in best or rank > best[key][0]:
            best[key] = (rank, job)
    return [job for _rank, job in best.values()]


def merge(previous, jobs: list, statuses: list, today: str, generated_at: str) -> dict:
    previous = previous or {}
    prev_jobs = {j["id"]: j for j in previous.get("jobs", [])}
    prev_status = {s["key"]: s for s in previous.get("sources", [])}

    fresh = {}
    for job in jobs:
        old = prev_jobs.get(job["id"])
        job["firstSeen"] = (old or {}).get("firstSeen", today)
        job["lastSeen"] = today
        fresh[job["id"]] = job

    cutoff = (dt.date.fromisoformat(today) - dt.timedelta(days=CARRY_DAYS)).isoformat()
    carried, out_status = {}, []
    for status in statuses:
        status = dict(status)
        if status["status"] == "ok":
            status["lastOk"] = today
        else:
            status["lastOk"] = prev_status.get(status["key"], {}).get("lastOk", "")
            kept = [j for j in prev_jobs.values()
                    if j.get("source") == status["key"] and j["id"] not in fresh
                    and j.get("lastSeen", "") >= cutoff]
            for job in kept:
                carried[job["id"]] = job
            if kept:
                status["carried"] = len(kept)
        out_status.append(status)

    merged = [j for j in [*fresh.values(), *carried.values()]
              if not (j.get("closing") and j["closing"] < today)]
    merged = dedupe(merged)
    merged.sort(key=lambda j: (j.get("posted") or j["firstSeen"], j["firstSeen"]), reverse=True)
    out_status.sort(key=lambda s: (s["government"], s["label"]))
    return {"generatedAt": generated_at, "jobs": merged, "sources": out_status}


def collect_all():
    jobs, statuses = [], []
    with ThreadPoolExecutor(max_workers=6) as pool:
        portal_futures = [pool.submit(portals.collect_portal, s) for s in portals.SOURCES]
        # Job Bank groups run one after another to stay polite to a public service.
        bank_future = pool.submit(lambda: [jobbank.collect_group(g) for g in jobbank.GROUPS])
        gojobs_future = pool.submit(gojobs.collect)
        for future in portal_futures:
            found, status = future.result()
            jobs.extend(found)
            statuses.append(status)
        found, status = gojobs_future.result()
        jobs.extend(found)
        statuses.append(status)
        for found, status in bank_future.result():
            jobs.extend(found)
            statuses.append(status)
    return jobs, statuses


def main() -> int:
    previous = None
    if OUTPUT.exists():
        try:
            previous = json.loads(OUTPUT.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = None
    jobs, statuses = collect_all()
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    result = merge(previous, jobs, statuses, TODAY, now)
    for status in result["sources"]:
        extra = f", {status['carried']} carried over" if status.get("carried") else ""
        print(f"{status['label']}: {status['status']} ({status['count']}{extra})")
    if not result["jobs"]:
        print("No postings available; leaving data/jobs.json untouched.", file=sys.stderr)
        return 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Wrote {len(result['jobs'])} postings.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
