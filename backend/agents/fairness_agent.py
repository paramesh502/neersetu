"""
Flow & Fairness Agent — computes the Fair Water Opportunity Score (FWOS).

Formula components:
  1. Downstream Penalty  = (canal_position - 1) / (max_position - 1)   × 30
  2. Efficiency Deficit  = (1 - η)                                       × 20
  3. Historical Deficit  = min(historical_deficit / 5.0, 1)              × 25
  4. Missed Turns        = min(missed_turns / 5, 1)                      × 15
  5. Crop Urgency        = urgency_weight                                 × 10

FWOS = sum of components, scaled 0–100.
"""
from agents.state import NeerSetuState, AgentStep

URGENCY_WEIGHTS = {
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.5,
    "low": 0.25,
}

MAX_CANAL_POSITION = 6


def compute_fwos(
    canal_position: int,
    eta: float,
    historical_deficit: float,
    missed_turns: int,
    urgency: str,
    max_position: int = MAX_CANAL_POSITION,
) -> tuple[float, dict]:
    """Return (score, breakdown_dict)."""

    # Component 1: downstream penalty (higher position = more disadvantaged)
    if max_position > 1:
        downstream_raw = (canal_position - 1) / (max_position - 1)
    else:
        downstream_raw = 0.0
    downstream_score = downstream_raw * 30

    # Component 2: flow efficiency deficit
    efficiency_score = (1 - eta) * 20

    # Component 3: historical water deficit
    deficit_score = min(historical_deficit / 5.0, 1.0) * 25

    # Component 4: missed turns
    missed_score = min(missed_turns / 5.0, 1.0) * 15

    # Component 5: crop urgency
    urgency_score = URGENCY_WEIGHTS.get(urgency, 0.5) * 10

    total = downstream_score + efficiency_score + deficit_score + missed_score + urgency_score

    breakdown = {
        "downstream_penalty": round(downstream_score, 2),
        "efficiency_deficit": round(efficiency_score, 2),
        "historical_deficit_score": round(deficit_score, 2),
        "missed_turns_score": round(missed_score, 2),
        "crop_urgency_score": round(urgency_score, 2),
        "total": round(total, 2),
        "inputs": {
            "canal_position": canal_position,
            "max_position": max_position,
            "eta": eta,
            "historical_deficit": historical_deficit,
            "missed_turns": missed_turns,
            "urgency": urgency,
        },
    }

    return round(total, 2), breakdown


def build_explanation(state: NeerSetuState, breakdown: dict) -> str:
    farmer = state.get("farmer_name", "Farmer")
    plot = state.get("extracted_plot", "Unknown Plot")
    crop = state.get("extracted_crop", "crop")
    fwos = breakdown["total"]
    pos = breakdown["inputs"]["canal_position"]
    eta = breakdown["inputs"]["eta"]
    deficit = breakdown["inputs"]["historical_deficit"]
    urgency = breakdown["inputs"]["urgency"]

    lines = [
        f'"{plot} received priority because:',
        f"• Downstream position #{pos} detected — penalty applied",
        f"• Flow Efficiency Index (η) = {eta:.2f}",
        f"• Historical water deficit = {deficit:.1f} hours",
        f"• Crop urgency: {crop} rated {urgency}",
        f"• Missed turns factor included",
        f"",
        f'FWOS = {fwos}"',
    ]
    return "\n".join(lines)


def run_fairness_agent(state: NeerSetuState) -> NeerSetuState:
    step: AgentStep = {
        "agent": "Flow & Fairness Agent",
        "status": "running",
        "output": "",
        "details": {},
    }

    canal_position = state.get("canal_position") or 1
    eta = state.get("flow_efficiency_index") or 1.0
    historical_deficit = state.get("historical_deficit") or 0.0
    missed_turns = state.get("missed_turns") or 0
    urgency = state.get("extracted_urgency") or "medium"

    fwos, breakdown = compute_fwos(
        canal_position=canal_position,
        eta=eta,
        historical_deficit=historical_deficit,
        missed_turns=missed_turns,
        urgency=urgency,
    )

    explanation = build_explanation(state, breakdown)

    state["fwos_score"] = fwos
    state["fwos_breakdown"] = breakdown
    state["fairness_explanation"] = explanation

    step["status"] = "complete"
    step["output"] = f"FWOS computed: {fwos}/100 — priority rank assigned"
    step["details"] = breakdown

    steps = list(state.get("agent_steps", []))
    steps.append(step)
    state["agent_steps"] = steps
    return state
