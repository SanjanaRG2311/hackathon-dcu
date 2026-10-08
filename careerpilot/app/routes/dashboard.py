import threading

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import config, scheduler
from ..db import get_db
from ..models import STATUSES, Application, Job, Match, Profile, ScanRun
from ..web import templates

router = APIRouter()


@router.get("/")
def dashboard(request: Request, profile: int | None = None, db: Session = Depends(get_db)):
    q = db.query(Match).order_by(Match.final_score.desc())
    if profile:
        q = q.filter(Match.profile_id == profile)
    apps = db.query(Application).all()
    totals = db.query(func.coalesce(func.sum(ScanRun.scanned), 0), func.coalesce(func.sum(ScanRun.duplicates), 0),
                      func.coalesce(func.sum(ScanRun.alerted), 0)).one()
    stats = {"scanned": totals[0], "duplicates": totals[1], "alerts": totals[2], "jobs": db.query(Job).count(),
             "hours_saved": round(totals[0] * 3 / 60, 1)}
    return templates.TemplateResponse(request, "dashboard.html", {
        "matches": q.limit(60).all(), "profiles": db.query(Profile).all(), "active": profile, "stats": stats,
        "board": {s: [a for a in apps if a.status == s] for s in STATUSES}, "statuses": STATUSES,
        "runs": db.query(ScanRun).order_by(ScanRun.id.desc()).limit(5).all(), "live": config.LIVE_SOURCES,
        "state": scheduler.STATE, "stages": scheduler.STAGES})


@router.get("/pipeline")
def pipeline(request: Request):
    return templates.TemplateResponse(request, "_pipeline.html", {"state": scheduler.STATE, "stages": scheduler.STAGES})


@router.post("/scan")
def scan(demo: int = 0):
    if not scheduler.STATE["running"]:
        threading.Thread(target=scheduler.run_scan, args=(bool(demo),), daemon=True).start()
    return RedirectResponse("/", status_code=303)


@router.get("/review/{aid}")
def review(aid: int, request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "review.html", {"app": db.get(Application, aid)})


@router.post("/review/{aid}/approve")
def approve(aid: int, db: Session = Depends(get_db)):
    a = db.get(Application, aid)
    if a:
        a.approved, a.status = True, "Approved"
        db.commit()
    return RedirectResponse("/", status_code=303)


@router.post("/applications/{aid}/status")
def set_status(aid: int, status: str, db: Session = Depends(get_db)):
    a = db.get(Application, aid)
    if a and status in STATUSES:
        a.status = status
        db.commit()
    return RedirectResponse("/", status_code=303)
