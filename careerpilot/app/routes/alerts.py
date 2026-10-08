from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..agents.notifier import send_telegram
from ..db import get_db
from ..models import Alert
from ..web import templates

router = APIRouter(prefix="/alerts")


@router.get("")
def alerts(request: Request, db: Session = Depends(get_db)):
    rows = db.query(Alert).order_by(Alert.id.desc()).limit(100).all()
    return templates.TemplateResponse(request, "alerts.html", {"alerts": rows})


@router.post("/test")
def test_alert(db: Session = Depends(get_db)):
    ok, info = send_telegram("CareerPilot test notification")
    db.add(Alert(channel="telegram", ok=ok, message=f"Test notification [{info}]"))
    db.commit()
    return RedirectResponse("/alerts", status_code=303)
