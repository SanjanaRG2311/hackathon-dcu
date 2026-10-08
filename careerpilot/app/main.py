from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from . import scheduler
from .db import SessionLocal, init_db
from .models import Profile
from .routes import alerts, dashboard, profiles

SEED = [
    dict(name="PMO - Dublin", role="PMO Analyst", alt_titles="PMO Manager, PMO Lead", job_type="Part-time",
         locations="Dublin", keywords="PMO, Governance, Reporting, RAID", experience=10),
    dict(name="Project Manager - Cork", role="Project Manager", alt_titles="Delivery Lead, Programme Manager",
         job_type="Full-time", locations="Cork", keywords="Delivery, Stakeholder Management, Agile, Waterfall",
         experience=8),
    dict(name="Scrum Master - Limerick", role="Scrum Master", alt_titles="Agile Coach", job_type="Part-time",
         locations="Limerick", keywords="Scrum, Agile Coach, Sprint Planning", experience=6),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as db:
        if not db.query(Profile).count():
            db.add_all(Profile(**s) for s in SEED)
            db.commit()
    scheduler.start()
    yield
    scheduler.scheduler.shutdown(wait=False)


app = FastAPI(title="CareerPilot", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
app.include_router(dashboard.router)
app.include_router(profiles.router)
app.include_router(alerts.router)
