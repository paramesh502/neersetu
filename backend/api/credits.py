from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from models.models import WaterCredit, Farmer, CreditStatus
from db.database import get_session

router = APIRouter(prefix="/credits", tags=["Water Credits"])


class CreditRead(BaseModel):
    id: int
    credit_id: str
    giving_farmer_id: Optional[int]
    giving_farmer_name: Optional[str]
    receiving_farmer_id: Optional[int]
    receiving_farmer_name: Optional[str]
    hours_given: float
    hours_owed: float
    status: str
    notes: Optional[str]
    created_at: datetime
    redeemed_at: Optional[datetime]

    class Config:
        from_attributes = True


@router.get("/", response_model=List[CreditRead])
def list_credits(session: Session = Depends(get_session)):
    credits = session.exec(
        select(WaterCredit).order_by(WaterCredit.created_at.desc())
    ).all()
    return _enrich(credits, session)


@router.get("/farmer/{farmer_id}", response_model=List[CreditRead])
def credits_for_farmer(farmer_id: str, session: Session = Depends(get_session)):
    farmer = session.exec(
        select(Farmer).where(Farmer.farmer_id == farmer_id)
    ).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")

    credits = session.exec(
        select(WaterCredit).where(
            (WaterCredit.giving_farmer_id == farmer.id)
            | (WaterCredit.receiving_farmer_id == farmer.id)
        ).order_by(WaterCredit.created_at.desc())
    ).all()
    return _enrich(credits, session)


@router.patch("/{credit_id}/redeem")
def redeem_credit(credit_id: str, session: Session = Depends(get_session)):
    credit = session.exec(
        select(WaterCredit).where(WaterCredit.credit_id == credit_id)
    ).first()
    if not credit:
        raise HTTPException(status_code=404, detail="Credit not found")
    if credit.status != CreditStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"Credit is already {credit.status}")

    credit.status = CreditStatus.REDEEMED
    credit.redeemed_at = datetime.utcnow()

    # Update receiving farmer's balance
    if credit.receiving_farmer_id:
        farmer = session.get(Farmer, credit.receiving_farmer_id)
        if farmer:
            farmer.water_credit_balance = max(0, farmer.water_credit_balance - credit.hours_owed)
            session.add(farmer)

    session.add(credit)
    session.commit()
    return {"message": f"Credit {credit_id} redeemed", "hours_owed": credit.hours_owed}


@router.get("/summary")
def credits_summary(session: Session = Depends(get_session)):
    credits = session.exec(select(WaterCredit)).all()
    total_given = sum(c.hours_given for c in credits)
    total_owed = sum(c.hours_owed for c in credits)
    active = [c for c in credits if c.status == CreditStatus.ACTIVE]
    redeemed = [c for c in credits if c.status == CreditStatus.REDEEMED]
    return {
        "total_credits": len(credits),
        "active_credits": len(active),
        "redeemed_credits": len(redeemed),
        "total_hours_given": round(total_given, 2),
        "total_hours_owed": round(total_owed, 2),
        "net_compensation": round(total_owed - total_given, 2),
    }


def _enrich(credits, session: Session) -> List[CreditRead]:
    results = []
    for c in credits:
        giver = session.get(Farmer, c.giving_farmer_id) if c.giving_farmer_id else None
        receiver = session.get(Farmer, c.receiving_farmer_id) if c.receiving_farmer_id else None
        results.append(CreditRead(
            id=c.id,
            credit_id=c.credit_id,
            giving_farmer_id=c.giving_farmer_id,
            giving_farmer_name=giver.name if giver else None,
            receiving_farmer_id=c.receiving_farmer_id,
            receiving_farmer_name=receiver.name if receiver else None,
            hours_given=c.hours_given,
            hours_owed=c.hours_owed,
            status=c.status,
            notes=c.notes,
            created_at=c.created_at,
            redeemed_at=c.redeemed_at,
        ))
    return results
