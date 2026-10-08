import json
import re
from difflib import SequenceMatcher

from sqlalchemy.orm import Session

from ..models import Job


def _n(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()


def _same(a: dict | Job, b: Job) -> bool:
    get = (lambda o, k: o[k]) if isinstance(a, dict) else getattr
    if _n(get(a, "company")) != _n(b.company):
        return False
    if _n(get(a, "location").split(",")[0]) != _n(b.location.split(",")[0]):
        return False
    return SequenceMatcher(None, _n(get(a, "title")), _n(b.title)).ratio() >= 0.85


def dedupe(jobs: list[dict], db: Session) -> tuple[list[Job], int]:
    pool = db.query(Job).all()
    resolved: list[Job] = []
    dupes = 0
    for j in jobs:
        link = {"source": j["source"], "url": j["url"]}
        hit = next((e for e in pool if _same(j, e)), None)
        if hit:
            dupes += 1
            links = hit.sources
            if link not in links:
                hit.sources_json = json.dumps(links + [link])
        else:
            hit = Job(title=j["title"], company=j["company"], location=j["location"], job_type=j["job_type"],
                      description=j["description"], url=j["url"], posted_at=j["posted_at"],
                      sources_json=json.dumps([link]))
            db.add(hit)
            pool.append(hit)
        if hit not in resolved:
            resolved.append(hit)
    db.flush()
    return resolved, dupes
