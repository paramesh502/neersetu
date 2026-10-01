from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class CropType(str, Enum):
    SUGARCANE = "Sugarcane"
    WHEAT = "Wheat"
    RICE = "Rice"
    COTTON = "Cotton"
    MAIZE = "Maize"
    VEGETABLES = "Vegetables"


class RequestStatus(str, Enum):
    PENDING = "pending"
    NEGOTIATING = "negotiating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"


class SwapStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"


class CreditStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REDEEMED = "redeemed"
    EXPIRED = "expired"


class NotificationChannel(str, Enum):
    CHAT = "chat"
    SMS = "sms"
    IVR = "ivr"
    PRINT = "print"


# ─── Farmer ───────────────────────────────────────────────────────────────────

class Farmer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    farmer_id: str = Field(unique=True, index=True)
    name: str
    phone: str
    plot_number: str = Field(unique=True)
    canal_position: int          # 1 = most upstream
    crop_type: CropType
    flow_efficiency_index: float  # η: 0.0–1.0
    water_credit_balance: float = Field(default=0.0)
    total_hours_allocated: float = Field(default=0.0)
    total_hours_used: float = Field(default=0.0)
    historical_deficit: float = Field(default=0.0)
    missed_turns: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    schedules: List["IrrigationSchedule"] = Relationship(back_populates="farmer")
    emergency_requests: List["EmergencyRequest"] = Relationship(back_populates="farmer")
    credits_given: List["WaterCredit"] = Relationship(
        back_populates="giving_farmer",
        sa_relationship_kwargs={"foreign_keys": "[WaterCredit.giving_farmer_id]"},
    )
    credits_received: List["WaterCredit"] = Relationship(
        back_populates="receiving_farmer",
        sa_relationship_kwargs={"foreign_keys": "[WaterCredit.receiving_farmer_id]"},
    )


# ─── Irrigation Schedule ──────────────────────────────────────────────────────

class IrrigationSchedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    farmer_id: Optional[int] = Field(default=None, foreign_key="farmer.id")
    slot_start: datetime
    slot_end: datetime
    hours_allocated: float
    hours_used: float = Field(default=0.0)
    status: str = Field(default="scheduled")   # scheduled | active | completed | swapped
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    farmer: Optional[Farmer] = Relationship(back_populates="schedules")


# ─── Emergency Request ────────────────────────────────────────────────────────

class EmergencyRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    farmer_id: Optional[int] = Field(default=None, foreign_key="farmer.id")
    raw_message: str
    extracted_crop: Optional[str] = None
    extracted_urgency: Optional[str] = None   # low | medium | high | critical
    extracted_hours: Optional[float] = None
    extracted_plot: Optional[str] = None
    status: RequestStatus = Field(default=RequestStatus.PENDING)
    fwos_score: Optional[float] = None        # Fair Water Opportunity Score
    resolution_summary: Optional[str] = None
    decision_trace: Optional[str] = None      # JSON string of agent chain
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    farmer: Optional[Farmer] = Relationship(back_populates="emergency_requests")
    negotiation: Optional["NegotiationRecord"] = Relationship(back_populates="emergency_request")


# ─── Negotiation Record ───────────────────────────────────────────────────────

class NegotiationRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    emergency_request_id: Optional[int] = Field(default=None, foreign_key="emergencyrequest.id")
    requesting_farmer_id: Optional[int] = Field(default=None, foreign_key="farmer.id")
    yielding_farmer_id: Optional[int] = Field(default=None, foreign_key="farmer.id")
    hours_requested: float
    hours_yielded: float
    compensation_hours: float       # hours owed back
    yielding_farmer_eta: float
    receiving_farmer_eta: float
    proposal_text: str
    status: SwapStatus = Field(default=SwapStatus.PROPOSED)
    agent_steps: Optional[str] = None   # JSON steps from LangGraph
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    emergency_request: Optional[EmergencyRequest] = Relationship(back_populates="negotiation")


# ─── Water Credit ─────────────────────────────────────────────────────────────

class WaterCredit(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    credit_id: str = Field(unique=True)
    giving_farmer_id: Optional[int] = Field(default=None, foreign_key="farmer.id")
    receiving_farmer_id: Optional[int] = Field(default=None, foreign_key="farmer.id")
    negotiation_id: Optional[int] = Field(default=None, foreign_key="negotiationrecord.id")
    hours_given: float
    hours_owed: float
    status: CreditStatus = Field(default=CreditStatus.ACTIVE)
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    redeemed_at: Optional[datetime] = None

    giving_farmer: Optional[Farmer] = Relationship(
        back_populates="credits_given",
        sa_relationship_kwargs={"foreign_keys": "[WaterCredit.giving_farmer_id]"},
    )
    receiving_farmer: Optional[Farmer] = Relationship(
        back_populates="credits_received",
        sa_relationship_kwargs={"foreign_keys": "[WaterCredit.receiving_farmer_id]"},
    )


# ─── Notification Log ─────────────────────────────────────────────────────────

class NotificationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    farmer_id: Optional[int] = Field(default=None, foreign_key="farmer.id")
    negotiation_id: Optional[int] = Field(default=None, foreign_key="negotiationrecord.id")
    channel: NotificationChannel
    message_text: str
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    delivered: bool = Field(default=False)


# ─── Audit Log ────────────────────────────────────────────────────────────────

class AuditLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str        # swap_proposed | swap_accepted | credit_issued | schedule_changed
    actor: str             # agent name or farmer id
    description: str
    metadata_json: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
