from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from models.models import AuditLog
from db.database import get_session

router = APIRouter(prefix="/audit", tags=["Audit Log"])


class AuditRead(BaseModel):
    id: int
    event_type: str
    actor: str
    description: str
    metadata_json: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[AuditRead])
def list_audit(limit: int = 50, session: Session = Depends(get_session)):
    logs = session.exec(
        select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    ).all()
    return logs


@router.get("/stats")
def audit_stats(session: Session = Depends(get_session)):
    logs = session.exec(select(AuditLog)).all()
    event_counts: dict = {}
    for log in logs:
        event_counts[log.event_type] = event_counts.get(log.event_type, 0) + 1
    return {
        "total_events": len(logs),
        "event_breakdown": event_counts,
    }
