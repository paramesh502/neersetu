"""
Intake Agent — extracts structured data from a farmer's free-text emergency message.
Falls back to rule-based heuristics if LLM is unavailable.
"""
import json
import re
import os
from agents.state import NeerSetuState, AgentStep


CROP_KEYWORDS = {
    "sugarcane": "Sugarcane",
    "wheat": "Wheat",
    "rice": "Rice",
    "paddy": "Rice",
    "cotton": "Cotton",
    "maize": "Maize",
    "corn": "Maize",
    "vegetables": "Vegetables",
    "vegetable": "Vegetables",
    "onion": "Vegetables",
    "tomato": "Vegetables",
}

URGENCY_KEYWORDS = {
    "dying": "critical",
    "drying": "critical",
    "drought": "critical",
    "emergency": "high",
    "urgent": "high",
    "today": "high",
    "soon": "medium",
    "need": "medium",
    "request": "low",
}


def _rule_based_extract(message: str) -> dict:
    msg_lower = message.lower()

    crop = None
    for kw, val in CROP_KEYWORDS.items():
        if kw in msg_lower:
            crop = val
            break

    urgency = "medium"
    for kw, val in URGENCY_KEYWORDS.items():
        if kw in msg_lower:
            urgency = val
            break

    hours = 3.0
    hour_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)", msg_lower)
    if hour_matches:
        hours = float(hour_matches[0])
    elif "half" in msg_lower:
        hours = 0.5

    plot = None
    plot_matches = re.findall(r"plot[- ]?(\d+)", msg_lower, re.IGNORECASE)
    if plot_matches:
        plot = f"Plot-{plot_matches[0]}"

    return {
        "extracted_crop": crop or "Unknown",
        "extracted_urgency": urgency,
        "extracted_hours": hours,
        "extracted_plot": plot,
    }


def _llm_extract(message: str, farmer_name: str) -> dict:
    try:
        from agents.llm import get_llm
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = get_llm(temperature=0.0)
        system = SystemMessage(content="""You are an irrigation assistant.
Extract structured information from a farmer's emergency irrigation request.
Return ONLY valid JSON with keys:
  extracted_crop (string),
  extracted_urgency (one of: low | medium | high | critical),
  extracted_hours (number, default 3.0),
  extracted_plot (string or null).
Do not add explanations.""")

        human = HumanMessage(content=f"Farmer: {farmer_name}\nMessage: {message}")
        response = llm.invoke([system, human])
        raw = response.content.strip()
        # Strip markdown fences if present
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
        return json.loads(raw)
    except Exception:
        return {}


def run_intake_agent(state: NeerSetuState) -> NeerSetuState:
    step: AgentStep = {
        "agent": "Intake Agent",
        "status": "running",
        "output": "",
        "details": {},
    }

    message = state.get("raw_message", "")
    farmer_name = state.get("farmer_name", "Unknown Farmer")

    # Try LLM first, fall back to rule-based
    result = {}
    use_llm = bool(os.getenv("GROQ_API_KEY", "").startswith("gsk_"))
    if use_llm:
        result = _llm_extract(message, farmer_name)

    if not result or "extracted_crop" not in result:
        result = _rule_based_extract(message)

    state["extracted_crop"] = result.get("extracted_crop", "Unknown")
    state["extracted_urgency"] = result.get("extracted_urgency", "medium")
    state["extracted_hours"] = float(result.get("extracted_hours") or 3.0)
    state["extracted_plot"] = result.get("extracted_plot") or state.get("extracted_plot")

    step["status"] = "complete"
    step["output"] = (
        f"Extracted: crop={state['extracted_crop']}, "
        f"urgency={state['extracted_urgency']}, "
        f"hours={state['extracted_hours']}, "
        f"plot={state['extracted_plot']}"
    )
    step["details"] = result

    steps = list(state.get("agent_steps", []))
    steps.append(step)
    state["agent_steps"] = steps
    return state
