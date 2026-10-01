"""Seed the database with demo farmers and schedules."""
from datetime import datetime, timedelta
from sqlmodel import Session, select
from db.database import engine, init_db
from models.models import (
    Farmer, IrrigationSchedule, AuditLog, CropType, WaterCredit, CreditStatus
)
import uuid

FARMERS_DATA = [
    {
        "farmer_id": "F001",
        "name": "Arjun Patil",
        "phone": "+91-9876543201",
        "plot_number": "Plot-1",
        "canal_position": 1,
        "crop_type": CropType.WHEAT,
        "flow_efficiency_index": 1.0,
        "historical_deficit": 0.0,
        "missed_turns": 0,
        "water_credit_balance": 0.0,
    },
    {
        "farmer_id": "F002",
        "name": "Bharat Sharma",
        "phone": "+91-9876543202",
        "plot_number": "Plot-2",
        "canal_position": 2,
        "crop_type": CropType.RICE,
        "flow_efficiency_index": 0.95,
        "historical_deficit": 0.5,
        "missed_turns": 0,
        "water_credit_balance": 0.0,
    },
    {
        "farmer_id": "F003",
        "name": "Chandrakant Desai",
        "phone": "+91-9876543203",
        "plot_number": "Plot-3",
        "canal_position": 3,
        "crop_type": CropType.COTTON,
        "flow_efficiency_index": 0.88,
        "historical_deficit": 0.8,
        "missed_turns": 1,
        "water_credit_balance": 0.0,
    },
    {
        "farmer_id": "F004",
        "name": "Dinesh Kumar",
        "phone": "+91-9876543204",
        "plot_number": "Plot-4",
        "canal_position": 4,
        "crop_type": CropType.MAIZE,
        "flow_efficiency_index": 0.80,
        "historical_deficit": 1.2,
        "missed_turns": 1,
        "water_credit_balance": 0.0,
    },
    {
        "farmer_id": "F005",
        "name": "Eknath Jadhav",
        "phone": "+91-9876543205",
        "plot_number": "Plot-5",
        "canal_position": 5,
        "crop_type": CropType.VEGETABLES,
        "flow_efficiency_index": 0.72,
        "historical_deficit": 1.8,
        "missed_turns": 2,
        "water_credit_balance": 0.0,
    },
    {
        "farmer_id": "F006",
        "name": "Farukh Mirza",
        "phone": "+91-9876543206",
        "plot_number": "Plot-6",
        "canal_position": 6,
        "crop_type": CropType.SUGARCANE,
        "flow_efficiency_index": 0.65,
        "historical_deficit": 2.5,
        "missed_turns": 3,
        "water_credit_balance": 0.0,
    },
]

# Base time: tomorrow 06:00
BASE_TIME = datetime.utcnow().replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(days=1)


def seed():
    init_db()
    with Session(engine) as session:
        existing = session.exec(select(Farmer)).first()
        if existing:
            print("Database already seeded. Skipping.")
            return

        farmers = []
        for data in FARMERS_DATA:
            farmer = Farmer(**data)
            session.add(farmer)
            farmers.append(farmer)
        session.commit()
        for f in farmers:
            session.refresh(f)

        # Assign 3-hour rotating slots starting tomorrow
        slot_cursor = BASE_TIME
        for farmer in farmers:
            schedule = IrrigationSchedule(
                farmer_id=farmer.id,
                slot_start=slot_cursor,
                slot_end=slot_cursor + timedelta(hours=3),
                hours_allocated=3.0,
                status="scheduled",
            )
            session.add(schedule)
            slot_cursor += timedelta(hours=3)

        # Add a few historical credits
        giving = farmers[2]   # F003 – Plot 3
        receiving = farmers[4]  # F005 – Plot 5
        credit = WaterCredit(
            credit_id=f"CR-{uuid.uuid4().hex[:8].upper()}",
            giving_farmer_id=giving.id,
            receiving_farmer_id=receiving.id,
            hours_given=1.5,
            hours_owed=1.88,   # 1.5 * 0.88 / 0.72
            status=CreditStatus.ACTIVE,
            notes="Historical swap: Plot-3 yielded to Plot-5",
        )
        session.add(credit)

        session.add(AuditLog(
            event_type="system_seed",
            actor="system",
            description="Database seeded with 6 demo farmers and initial schedules.",
        ))
        session.commit()
        print("✅ Database seeded successfully.")


if __name__ == "__main__":
    seed()
