import io

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Profile
from ..web import templates

router = APIRouter(prefix="/profiles")


def parse_resume(name: str, data: bytes) -> str:
    try:
        if name.lower().endswith(".pdf"):
            from pypdf import PdfReader

            return "\n".join(pg.extract_text() or "" for pg in PdfReader(io.BytesIO(data)).pages)
        if name.lower().endswith(".docx"):
            from docx import Document

            return "\n".join(p.text for p in Document(io.BytesIO(data)).paragraphs)
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


@router.get("")
def list_profiles(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "profiles.html", {"profiles": db.query(Profile).all(), "edit": None})


@router.get("/{pid}/edit")
def edit_profile(pid: int, request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request, "profiles.html",
                                      {"profiles": db.query(Profile).all(), "edit": db.get(Profile, pid)})


@router.post("")
@router.post("/{pid}")
async def save_profile(pid: int | None = None, name: str = Form(...), role: str = Form(...),
                       alt_titles: str = Form(""), job_type: str = Form("Full-time"), locations: str = Form(""),
                       keywords: str = Form(""), experience: int = Form(0), min_score: int = Form(85),
                       resume: UploadFile | None = File(None), db: Session = Depends(get_db)):
    p = db.get(Profile, pid) if pid else Profile()
    p.name, p.role, p.alt_titles, p.job_type = name, role, alt_titles, job_type
    p.locations, p.keywords, p.experience, p.min_score = locations, keywords, experience, min_score
    if resume and resume.filename:
        text = parse_resume(resume.filename, await resume.read())
        if text:
            p.resume_text = text
    db.add(p)
    db.commit()
    return RedirectResponse("/profiles", status_code=303)


@router.post("/{pid}/delete")
def delete_profile(pid: int, db: Session = Depends(get_db)):
    p = db.get(Profile, pid)
    if p:
        db.delete(p)
        db.commit()
    return RedirectResponse("/profiles", status_code=303)
