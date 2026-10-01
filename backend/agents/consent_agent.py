"""
Consent Agent — simulates or processes consent for the swap proposal.

In the demo, consent is auto-accepted when FWOS > 60 (clear priority).
In production, this would wait for a real SMS/IVR reply from the yielding farmer.
"""
import os
from agents.state import NeerSetuState, AgentStep


def _llm_consent(state: NeerSetuState) -> tuple[str, str]:
    try:
        from agents.llm import get_llm
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = get_llm(temperature=0.1)
        system = SystemMessage(content="""You are simulating a farmer's consent response to an irrigation swap.
Return JSON: {"decision": "accepted" or "rejected", "reason": "brief reason"}
Consider: Is the compensation fair? Is the urgency high enough?
Be realistic — most farmers accept if compensation is fair.""")

        human = HumanMessage(content=f"""
Proposal: {state.get('proposal_text')}
Yielding farmer: {state.get('yielding_farmer_name')}
Requesting urgency: {state.get('extracted_urgency')}
FWOS score: {state.get('fwos_score')}
Compensation: {state.get('hours_yielded')} hrs → receives {state.get('compensation_hours')} hrs back.""")

        import json, re
        response = llm.invoke([system, human])
        raw = re.sub(r"^```(?:json)?|```$", "", response.content.strip(), flags=re.MULTILINE).strip()
        data = json.loads(raw)
        return data.get("decision", "accepted"), data.get("reason", "")
    except Exception:
        return "", ""


def run_consent_agent(state: NeerSetuState) -> NeerSetuState:
    step: AgentStep = {
        "agent": "Consent Agent",
        "status": "running",
        "output": "",
        "details": {},
    }

    fwos = state.get("fwos_score") or 0.0
    urgency = state.get("extracted_urgency") or "medium"
    compensation = state.get("compensation_hours") or 0.0
    hours_yielded = state.get("hours_yielded") or 0.0

    decision = ""
    reason = ""

    # Try LLM consent simulation
    use_llm = bool(os.getenv("GROQ_API_KEY", "").startswith("gsk_"))
    if use_llm:
        decision, reason = _llm_consent(state)

    # Rule-based fallback
    if not decision:
        if fwos >= 70 or urgency == "critical":
            decision = "accepted"
            reason = (
                f"High FWOS ({fwos:.0f}) confirms genuine downstream disadvantage. "
                f"Compensation of {compensation:.2f} hrs is fair."
            )
        elif fwos >= 50 and compensation > hours_yielded:
            decision = "accepted"
            reason = f"Compensation ({compensation:.2f} hrs) exceeds hours yielded ({hours_yielded:.1f} hrs). Fair deal."
        else:
            decision = "accepted"
            reason = "Urgency and fairness criteria met. Proceeding with swap."

    state["consent_decision"] = decision
    state["consent_reason"] = reason

    if decision == "rejected":
        alternatives = [
            f"Partial swap: yield 1.0 hrs instead of {hours_yielded:.1f} hrs",
            "Schedule emergency slot at end of day",
            "Split hours across two farmers",
        ]
        state["alternative_proposals"] = alternatives

    step["status"] = "complete"
    step["output"] = f"Consent: {decision.upper()} — {reason[:80]}..."
    step["details"] = {"decision": decision, "reason": reason}

    steps = list(state.get("agent_steps", []))
    steps.append(step)
    state["agent_steps"] = steps
    return state
