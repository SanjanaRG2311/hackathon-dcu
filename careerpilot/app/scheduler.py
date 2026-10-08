import json
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler

from . import config
from .agents.applier import draft
from .agents.dedupe import dedupe
from .agents.discovery import discover
from .agents.matcher import match
from .agents.normalizer import normalize
from .agents.notifier import notify
from .db import SessionLocal
from .models import Match, Profile, ScanRun

STAGES = ["Discovered", "Normalized", "Deduplicated", "Matched", "Notified"]
STATE: dict = {"running": False, "stage": "idle", "counts": {s: 0 for s in STAGES}, "log": [], "demo": False}
_lock = threading.Lock()
scheduler = BackgroundScheduler()


def _set(stage: str, key: str | None = None, n: int = 0, delay: float = 0) -> None:
    STATE["stage"] = stage
    if key:
        STATE["counts"][key] += n
    if delay:
        time.sleep(delay)


def run_scan(demo: bool = False) -> None:
    if not _lock.acquire(blocking=False):
        return
    delay = 0.9 if demo else 0
    STATE.update(running=True, stage="starting", counts={s: 0 for s in STAGES}, log=[], demo=demo)
    db = SessionLocal()
    run = ScanRun(demo=demo, scanned=0, duplicates=0, matched=0, alerted=0)
    try:
        for p in db.query(Profile).all():
            log = STATE["log"]
            raw = discover(p, demo, log)
            _set("Discovered", "Discovered", len(raw), delay)
            run.scanned += len(raw)
            norm = [n for n in (normalize(r) for r in raw) if n]
            _set("Normalized", "Normalized", len(norm), delay)
            jobs, dupes = dedupe(norm, db)
            run.duplicates += dupes
            _set("Deduplicated", "Deduplicated", dupes, delay)
            done = {m.job_id for m in db.query(Match).filter_by(profile_id=p.id)}
            for j in [j for j in jobs if j.id not in done]:
                r = match(p, j, log)
                m = Match(profile_id=p.id, job_id=j.id, role_fit=r["role_fit"], location_fit=r["location_fit"],
                          type_fit=r["type_fit"], skills_fit=r["skills_fit"], final_score=r["final_score"],
                          reason=r.get("reason", ""), matched_json=json.dumps(r.get("matched_keywords", [])),
                          missing_json=json.dumps(r.get("missing_skills", [])))
                m.profile, m.job = p, j
                db.add(m)
                db.flush()
                run.matched += 1
                STATE["counts"]["Matched"] += 1
                if m.final_score >= p.min_score:
                    notify(m, db)
                    run.alerted += 1
                    STATE["counts"]["Notified"] += 1
                if m.final_score > 90:
                    draft(m, db)
            _set("Matched", delay=delay)
            db.commit()
        _set("Notified", delay=delay)
        db.add(run)
        db.commit()
        STATE["stage"] = "complete"
    except Exception as e:
        db.rollback()
        STATE["log"].append(f"Scan failed: {type(e).__name__}: {e}")
        STATE["stage"] = "failed"
    finally:
        db.close()
        STATE["running"] = False
        _lock.release()


def scheduled_scan() -> None:
    run_scan(demo=not config.LIVE_SOURCES)


def start() -> None:
    scheduler.add_job(scheduled_scan, "interval", minutes=config.SCAN_MINUTES, id="scan", replace_existing=True)
    if not scheduler.running:
        scheduler.start()
