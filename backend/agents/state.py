"""Shared state definition for the NeerSetu LangGraph pipeline."""
from typing import TypedDict, Optional, List, Any


class AgentStep(TypedDict):
    agent: str
    status: str          # running | complete | error
    output: str
    details: dict


class NeerSetuState(TypedDict):
    # Input
    raw_message: str
    farmer_id: str

    # Extracted by Intake Agent
    extracted_crop: Optional[str]
    extracted_urgency: Optional[str]
    extracted_hours: Optional[float]
    extracted_plot: Optional[str]
    farmer_name: Optional[str]
    canal_position: Optional[int]
    flow_efficiency_index: Optional[float]
    historical_deficit: Optional[float]
    missed_turns: Optional[int]

    # Fairness Agent output
    fwos_score: Optional[float]
    fwos_breakdown: Optional[dict]
    priority_rank: Optional[int]
    fairness_explanation: Optional[str]

    # Negotiation Agent output
    yielding_farmer_id: Optional[str]
    yielding_farmer_name: Optional[str]
    yielding_farmer_eta: Optional[float]
    hours_yielded: Optional[float]
    compensation_hours: Optional[float]
    proposal_text: Optional[str]
    negotiation_id: Optional[int]

    # Consent Agent output
    consent_decision: Optional[str]        # accepted | rejected
    consent_reason: Optional[str]
    alternative_proposals: Optional[List[str]]

    # Ledger Agent output
    credit_id: Optional[str]
    ledger_updated: Optional[bool]
    schedule_updated: Optional[bool]

    # Dispatcher Agent output
    chat_notification: Optional[str]
    sms_notification: Optional[str]
    ivr_script: Optional[str]
    print_schedule: Optional[str]

    # Pipeline meta
    agent_steps: List[AgentStep]
    error: Optional[str]
    completed: bool

    # DB references
    emergency_request_id: Optional[int]
    db_farmer_data: Optional[dict]        # raw farmer row from DB
    db_yielding_farmer_data: Optional[dict]
