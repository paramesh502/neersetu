"""
Dispatcher Agent — generates multi-channel notifications:
  • Chat message (rich, conversational)
  • SMS (concise, 160-char limit)
  • IVR script (spoken, structured pauses)
  • Printable schedule (plain text table)
"""
import os
from datetime import datetime, timedelta
from agents.state import NeerSetuState, AgentStep


def _chat_message(state: NeerSetuState) -> str:
    consent = state.get("consent_decision", "accepted")
    requesting = state.get("farmer_name", "Farmer")
    plot = state.get("extracted_plot", "Unknown Plot")
    crop = state.get("extracted_crop", "crop")
    yielding = state.get("yielding_farmer_name", "Yielding Farmer")
    hours = state.get("hours_yielded", 0)
    comp = state.get("compensation_hours", 0)
    credit = state.get("credit_id", "N/A")
    fwos = state.get("fwos_score", 0)

    if consent == "accepted":
        return (
            f"✅ *NeerSetu Swap Confirmed*\n\n"
            f"🌾 *Emergency Request Resolved*\n"
            f"Farmer: {requesting} | {plot} | Crop: {crop}\n"
            f"Fair Water Opportunity Score: *{fwos}/100*\n\n"
            f"💧 *Swap Details:*\n"
            f"• {yielding} yields *{hours:.1f} hours* now\n"
            f"• {requesting} receives water immediately\n"
            f"• {yielding} earns *{comp:.2f} hours* credit (Water Credit #{credit})\n\n"
            f"📋 *Decision Basis:*\n"
            f"{state.get('fairness_explanation', 'Flow-aware fairness score computed.')}\n\n"
            f"_All parties have been notified. Ledger updated._"
        )
    else:
        return (
            f"⚠️ *NeerSetu — Swap Proposal Rejected*\n\n"
            f"Request from {requesting} ({plot}) could not be resolved via swap.\n"
            f"Reason: {state.get('consent_reason', 'Not available')}\n\n"
            f"Alternative options are being evaluated."
        )


def _sms_message(state: NeerSetuState) -> str:
    requesting = state.get("farmer_name", "Farmer")
    yielding = state.get("yielding_farmer_name", "Farmer")
    hours = state.get("hours_yielded", 0)
    comp = state.get("compensation_hours", 0)
    credit = state.get("credit_id", "N/A")

    msg = (
        f"NEERSETU: Swap APPROVED. "
        f"{yielding} yields {hours:.1f}h to {requesting}. "
        f"Credit {comp:.2f}h issued (#{credit}). "
        f"Water starts soon."
    )
    return msg[:160]


def _ivr_script(state: NeerSetuState) -> str:
    requesting = state.get("farmer_name", "Farmer")
    yielding = state.get("yielding_farmer_name", "Farmer")
    hours = state.get("hours_yielded", 0)
    comp = state.get("compensation_hours", 0)
    credit = state.get("credit_id", "N/A")
    consent = state.get("consent_decision", "accepted")

    if consent == "accepted":
        script = f"""[NeerSetu IVR Script]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GREETING:
"Namaste. This is NeerSetu, your canal coordination system."

[PAUSE 1 second]

ANNOUNCEMENT:
"An emergency irrigation swap has been approved."

[PAUSE 0.5 seconds]

DETAILS:
"Farmer {requesting} has been granted {hours:.1f} hours of water immediately."

[PAUSE 0.5 seconds]

"Farmer {yielding} has yielded their slot and will receive {comp:.2f} compensated hours."

[PAUSE 0.5 seconds]

CREDIT:
"Water credit number {credit} has been issued to {yielding}."

[PAUSE 0.5 seconds]

CLOSING:
"Thank you for cooperating with NeerSetu's fair water distribution system."
"For assistance, press 1. To hear this again, press 2."

[END]"""
    else:
        script = f"""[NeerSetu IVR Script]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GREETING:
"Namaste. This is NeerSetu."

[PAUSE 1 second]

ANNOUNCEMENT:
"The emergency swap request from {requesting} was not approved at this time."

[PAUSE 0.5 seconds]

"Our team is evaluating alternative solutions."

[PAUSE 0.5 seconds]

CLOSING:
"Please await further notification. Thank you."

[END]"""

    return script


def _print_schedule(state: NeerSetuState) -> str:
    now = datetime.utcnow()
    base = now.replace(hour=6, minute=0, second=0, microsecond=0) + timedelta(days=1)

    farmers_data = [
        ("F001", "Arjun Patil",       "Plot-1", 1, "Wheat",      "06:00–09:00", "✓ Scheduled"),
        ("F002", "Bharat Sharma",     "Plot-2", 2, "Rice",       "09:00–12:00", "✓ Scheduled"),
        ("F003", "Chandrakant Desai", "Plot-3", 3, "Cotton",     "12:00–15:00", "✓ Scheduled"),
        ("F004", "Dinesh Kumar",      "Plot-4", 4, "Maize",      "15:00–18:00", "✓ Scheduled"),
        ("F005", "Eknath Jadhav",     "Plot-5", 5, "Vegetables", "18:00–21:00", "✓ Scheduled"),
    ]

    yielding = state.get("yielding_farmer_name", "")
    requesting = state.get("farmer_name", "")
    plot = state.get("extracted_plot", "")

    lines = [
        "═══════════════════════════════════════════════════════",
        "           NEERSETU IRRIGATION SCHEDULE",
        f"           Date: {(now + timedelta(days=1)).strftime('%d %B %Y')}",
        "═══════════════════════════════════════════════════════",
        f"{'ID':<6} {'Farmer':<20} {'Plot':<8} {'Crop':<12} {'Slot':<14} {'Status'}",
        "───────────────────────────────────────────────────────",
    ]
    for fid, name, plt, pos, crop, slot, status in farmers_data:
        s = "⚡ SWAPPED" if name == yielding else status
        lines.append(f"{fid:<6} {name:<20} {plt:<8} {crop:<12} {slot:<14} {s}")

    # Add requesting farmer's emergency slot
    lines.append(
        f"{'F006':<6} {requesting:<20} {plot:<8} {'Sugarcane':<12} {'EMERGENCY':<14} ⚡ ACTIVE"
    )
    lines += [
        "───────────────────────────────────────────────────────",
        f"Emergency swap approved. Credit #{state.get('credit_id', 'N/A')} issued.",
        "═══════════════════════════════════════════════════════",
    ]
    return "\n".join(lines)


def run_dispatcher_agent(state: NeerSetuState) -> NeerSetuState:
    step: AgentStep = {
        "agent": "Dispatcher Agent",
        "status": "running",
        "output": "",
        "details": {},
    }

    chat = _chat_message(state)
    sms = _sms_message(state)
    ivr = _ivr_script(state)
    schedule = _print_schedule(state)

    state["chat_notification"] = chat
    state["sms_notification"] = sms
    state["ivr_script"] = ivr
    state["print_schedule"] = schedule
    state["completed"] = True

    channels = ["Chat", "SMS", "IVR", "Print Schedule"]
    step["status"] = "complete"
    step["output"] = f"Notifications dispatched via: {', '.join(channels)}"
    step["details"] = {
        "channels": channels,
        "sms_length": len(sms),
        "chat_length": len(chat),
    }

    steps = list(state.get("agent_steps", []))
    steps.append(step)
    state["agent_steps"] = steps
    return state
