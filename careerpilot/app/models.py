import json
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

STATUSES = ["Found", "Approved", "Applied", "Interview", "Offer", "Rejected"]


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(120))
    alt_titles: Mapped[str] = mapped_column(Text, default="")
    job_type: Mapped[str] = mapped_column(String(40), default="Full-time")
    locations: Mapped[str] = mapped_column(Text, default="")
    keywords: Mapped[str] = mapped_column(Text, default="")
    experience: Mapped[int] = mapped_column(Integer, default=0)
    min_score: Mapped[int] = mapped_column(Integer, default=85)
    resume_text: Mapped[str] = mapped_column(Text, default="")


class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    company: Mapped[str] = mapped_column(String(200))
    location: Mapped[str] = mapped_column(String(200), default="")
    job_type: Mapped[str] = mapped_column(String(40), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(Text, default="")
    posted_at: Mapped[str] = mapped_column(String(40), default="")
    sources_json: Mapped[str] = mapped_column(Text, default="[]")

    @property
    def sources(self) -> list[dict]:
        return json.loads(self.sources_json)


class Match(Base):
    __tablename__ = "matches"
    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"))
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"))
    role_fit: Mapped[int] = mapped_column(Integer, default=0)
    location_fit: Mapped[int] = mapped_column(Integer, default=0)
    type_fit: Mapped[int] = mapped_column(Integer, default=0)
    skills_fit: Mapped[int] = mapped_column(Integer, default=0)
    final_score: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(Text, default="")
    matched_json: Mapped[str] = mapped_column(Text, default="[]")
    missing_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    profile: Mapped[Profile] = relationship()
    job: Mapped[Job] = relationship()

    @property
    def matched(self) -> list[str]:
        return json.loads(self.matched_json)

    @property
    def missing(self) -> list[str]:
        return json.loads(self.missing_json)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int | None] = mapped_column(ForeignKey("matches.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(40), default="telegram")
    ok: Mapped[bool] = mapped_column(Boolean, default=False)
    message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"))
    status: Mapped[str] = mapped_column(String(20), default="Found")
    cv_summary: Mapped[str] = mapped_column(Text, default="")
    cover_letter: Mapped[str] = mapped_column(Text, default="")
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str] = mapped_column(Text, default="")
    match: Mapped[Match] = relationship()


class ScanRun(Base):
    __tablename__ = "scan_runs"
    id: Mapped[int] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    demo: Mapped[bool] = mapped_column(Boolean, default=False)
    scanned: Mapped[int] = mapped_column(Integer, default=0)
    duplicates: Mapped[int] = mapped_column(Integer, default=0)
    matched: Mapped[int] = mapped_column(Integer, default=0)
    alerted: Mapped[int] = mapped_column(Integer, default=0)
