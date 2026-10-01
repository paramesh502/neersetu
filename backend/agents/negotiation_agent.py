"""
Negotiation Agent — finds the best farmer to yield water and computes compensated hours.

Compensation Formula:
  Compensated Hours = Yielded Hours × (Yielding η / Receiving η)

The yielding farmer must:
  1. Have an upcoming schedule slot
  2. Have a lower FWOS (less urgent need)
  3. Have η >= receiving farmer's η (upstream / more efficient)
"""
import os
import re
from agents.state import NeerSetuState, AgentStep


def compute_compensation(
    hours_yielded: float,
    yielding_eta: float,
    receiving_eta: float,
) -> float:
    """Return compensated hours owed back to the yielding farmer."""
    if receiving_eta <= 0:
        receiving_eta = 0.01
    return round(hours_yielded * (yielding_eta / receiving_eta), 2)


def _build_proposal_text(
    requesting_farmer: str,
    requesting_plot: str,
    yielding_farmer: str,
    yielding_plot: str,
    hours_requested: float,
    hours_yielded: float,
    compensation: float,
    yielding_eta: float,
    receiving_eta: float,
) -> str:
    return (
        f"SWAP PROPOSAL\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Requesting: {requesting_farmer} ({requesting_plot})\n"
        f"Yielding:   {yielding_farmer} ({yielding_plot})\n\n"
        f"Hours Requested:    {hours_requested:.1f} hrs\n"
        f"Hours Yielded:      {hours_yielded:.1f} hrs\n\n"
        f"Compensation Calculation:\n"
        f"  {hours_yielded:.1f} hrs × (η={yielding_eta:.2f} / η={receiving_eta:.2f})\n"
        f"  = {compensation:.2f} hrs owed back\n\n"
        f"\"{yielding_farmer} yields {hours_yielded:.1f} hours now and "
        f"receives {compensation:.2f} hours later.\""
    )


def _llm_propose(state: NeerSetuState, yielding_data: dict) -> str:
    try:
        from agents.llm import get_llm
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = get_llm(temperature=0.3)
        system = SystemMessage(content="""You are NeerSetu's negotiation agent.
Generate a fair, concise water-swap proposal in 3-4 sentences.
Be professional but empathetic to both farmers.""")

        human = HumanMessage(content=f"""
Requesting farmer: {state.get('farmer_name')} at {state.get('extracted_plot')} (η={state.get('flow_efficiency_index'):.2f})
Crop: {state.get('extracted_crop')}, Urgency: {state.get('extracted_urgency')}
Hours needed: {state.get('extracted_hours')}

Yielding farmer: {yielding_data['name']} at Plot-{yielding_data['canal_position']} (η={yielding_data['eta']:.2f})
Hours to yield: {state.get('extracted_hours')}
Compensation owed: {state.get('compensation_hours')} hours

Generate the proposal.""")

        response = llm.invoke([system, human])
        return response.content.strip()
    except Exception:
        return ""


def run_negotiation_agent(state: NeerSetuState) -> NeerSetuState:
    step: AgentStep = {
        "agent": "Negotiation Agent",
        "status": "running",
        "output": "",
        "details": {},
    }

    # The yielding farmer is resolved by the API using DB data
    # and injected into state["db_yielding_farmer_data"] before this runs
    yielding_data = state.get("db_yielding_farmer_data") or {}

    hours_requested = state.get("extracted_hours") or 3.0
    receiving_eta = state.get("flow_efficiency_index") or 1.0

    if not yielding_data:
        # Fallback: use the farmer right upstream
        step["status"] = "error"
        step["output"] = "No suitable yielding farmer found for negotiation."
        steps = list(state.get("agent_steps", []))
        steps.append(step)
        state["agent_steps"] = steps
        state["error"] = "No available farmer to negotiate with."
        return state

    yielding_eta = yielding_data.get("eta", 1.0)
    hours_yielded = min(hours_requested, 3.0)  # max 3-hour swap
    compensation = compute_compensation(hours_yielded, yielding_eta, receiving_eta)

    state["yielding_farmer_id"] = yielding_data.get("farmer_id")
    state["yielding_farmer_name"] = yielding_data.get("name")
    state["yielding_farmer_eta"] = yielding_eta
    state["hours_yielded"] = hours_yielded
    state["compensation_hours"] = compensation

    # Try LLM proposal, fall back to template
    use_llm = bool(os.getenv("GROQ_API_KEY", "").startswith("gsk_"))
    proposal = ""
    if use_llm:
        proposal = _llm_propose(state, yielding_data)

    if not proposal:
        proposal = _build_proposal_text(
            requesting_farmer=state.get("farmer_name", "Requesting Farmer"),
            requesting_plot=state.get("extracted_plot", "Unknown"),
            yielding_farmer=yielding_data.get("name", "Yielding Farmer"),
            yielding_plot=f"Plot-{yielding_data.get('canal_position', '?')}",
            hours_requested=hours_requested,
            hours_yielded=hours_yielded,
            compensation=compensation,
            yielding_eta=yielding_eta,
            receiving_eta=receiving_eta,
        )

    state["proposal_text"] = proposal

    step["status"] = "complete"
    step["output"] = (
        f"{yielding_data.get('name')} proposed to yield {hours_yielded:.1f} hrs; "
        f"compensation = {compensation:.2f} hrs"
    )
    step["details"] = {
        "yielding_farmer": yielding_data.get("name"),
        "hours_yielded": hours_yielded,
        "compensation_hours": compensation,
        "formula": f"{hours_yielded} × ({yielding_eta} / {receiving_eta}) = {compensation}",
    }

    steps = list(state.get("agent_steps", []))
    steps.append(step)
    state["agent_steps"] = steps
    return state
