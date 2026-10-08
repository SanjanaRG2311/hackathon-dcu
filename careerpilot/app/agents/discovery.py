import json
from pathlib import Path

import httpx

from .. import config
from ..models import Profile

DEMO_FILE = Path(__file__).resolve().parent.parent / "data" / "demo_jobs.json"


def build_queries(p: Profile) -> list[tuple[str, str]]:
    titles = [p.role] + [t.strip() for t in p.alt_titles.split(",") if t.strip()]
    locs = [l.strip() for l in p.locations.split(",") if l.strip()] or ["Ireland"]
    return [(t, l) for t in titles[:3] for l in locs[:2]]


def load_demo() -> list[dict]:
    return json.loads(DEMO_FILE.read_text())


def _adzuna(what: str, where: str) -> list[dict]:
    r = httpx.get(
        "https://api.adzuna.com/v1/api/jobs/ie/search/1",
        params={"app_id": config.ADZUNA_APP_ID, "app_key": config.ADZUNA_APP_KEY,
                "what": what, "where": where, "results_per_page": 20},
        timeout=20,
    )
    r.raise_for_status()
    return [{"source": "Adzuna", "title": j.get("title"), "company": (j.get("company") or {}).get("display_name"),
             "location": (j.get("location") or {}).get("display_name"), "job_type": j.get("contract_time") or "",
             "description": j.get("description"), "url": j.get("redirect_url"), "posted_at": j.get("created")}
            for j in r.json().get("results", [])]


def _reed(what: str, where: str) -> list[dict]:
    r = httpx.get(
        "https://www.reed.co.uk/api/1.0/search",
        params={"keywords": what, "locationName": where, "resultsToTake": 20},
        auth=(config.REED_API_KEY, ""), timeout=20,
    )
    r.raise_for_status()
    return [{"source": "Reed", "title": j.get("jobTitle"), "company": j.get("employerName"),
             "location": j.get("locationName"), "job_type": "Part-time" if j.get("partTime") else "Full-time",
             "description": j.get("jobDescription"), "url": j.get("jobUrl"), "posted_at": j.get("date")}
            for j in r.json().get("results", [])]


def discover(profile: Profile, demo: bool, log: list[str]) -> list[dict]:
    if demo:
        return load_demo()
    jobs: list[dict] = []
    for what, where in build_queries(profile):
        for enabled, fn, name in [(config.ADZUNA_APP_ID and config.ADZUNA_APP_KEY, _adzuna, "Adzuna"),
                                  (config.REED_API_KEY, _reed, "Reed")]:
            if not enabled:
                continue
            try:
                jobs += fn(what, where)
            except Exception as e:
                log.append(f"{name} failed for '{what} {where}': {type(e).__name__}")
    return jobs
