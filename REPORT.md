# NeerSetu — Complete Technical Report

**Autonomous Multi-Agent Canal Dispatcher and Conflict Resolver**

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Database Schema](#4-database-schema)
5. [Seed Data — Demo Farmers](#5-seed-data--demo-farmers)
6. [The Core Problem Solved](#6-the-core-problem-solved)
7. [FWOS — Fair Water Opportunity Score](#7-fwos--fair-water-opportunity-score)
8. [Compensation Formula](#8-compensation-formula)
9. [The 6-Agent LangGraph Pipeline](#9-the-6-agent-langgraph-pipeline)
10. [Pipeline Graph Structure](#10-pipeline-graph-structure)
11. [Backend API Routes](#11-backend-api-routes)
12. [Frontend Pages](#12-frontend-pages)
13. [Notification Channels](#13-notification-channels)
14. [Water Credit System](#14-water-credit-system)
15. [Audit Log](#15-audit-log)
16. [How a Request Flows End-to-End](#16-how-a-request-flows-end-to-end)
17. [Without an OpenAI Key](#17-without-an-openai-key)
18. [File Structure](#18-file-structure)

---

## 1. Project Overview

NeerSetu (Hindi: *Neer* = Water, *Setu* = Bridge) is an AI-powered system for managing shared canal irrigation. It replaces informal, dispute-prone scheduling with an autonomous multi-agent workflow that:

- Receives emergency irrigation requests in **plain language**
- Parses, evaluates, and scores them automatically
- Negotiates a voluntary **water swap** between farmers
- Issues tamper-proof **water credits** as compensation
- Notifies all parties via **Chat, SMS, IVR, and print**
- Records every action in an **immutable audit log**

The core innovation is that water is measured in **usable opportunity**, not clock hours. A downstream farmer receiving weaker flow gets proportionally more compensated hours when they yield their slot — this is the η-adjusted compensation formula.

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        NeerSetu System                           │
│                                                                  │
│   Browser (Next.js 15 — localhost:3000)                          │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  Dashboard │ Farmers │ Emergency │ Negotiation │ Canal   │  │
│   │  Credits   │                                             │  │
│   └──────────────────────┬───────────────────────────────────┘  │
│                           │ HTTP (axios)                         │
│   FastAPI Server (localhost:8000)                                │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  /dashboard  /farmers  /emergency  /negotiations         │  │
│   │  /schedules  /credits  /audit                            │  │
│   │                                                          │  │
│   │  POST /emergency/process                                 │  │
│   │       │                                                  │  │
│   │       ▼  LangGraph Pipeline                              │  │
│   │  [Intake] → [Fairness] → [Negotiation]                   │  │
│   │      → [Consent] → [Ledger] → [Dispatcher]               │  │
│   └──────────────────────┬───────────────────────────────────┘  │
│                           │ SQLModel ORM                         │
│   SQLite Database (neersetu.db)                                  │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │  farmer  irrigationschedule  emergencyrequest            │  │
│   │  negotiationrecord  watercredit  auditlog               │  │
│   └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend Framework | Next.js | 15.0.3 |
| UI Library | React | 18.3.1 |
| Language | TypeScript | 5.6.3 |
| Styling | Tailwind CSS | 3.4.14 |
| Charts | Recharts | 2.13.3 |
| State Management | Zustand | 5.0.0 |
| HTTP Client | Axios | 1.7.7 |
| Backend Framework | FastAPI | 0.115.0 |
| Server | Uvicorn | 0.30.6 |
| Language | Python | 3.11 |
| ORM | SQLModel | 0.0.21 |
| Database | SQLite | (built-in) |
| AI Orchestration | LangGraph | 0.2.28 |
| AI Framework | LangChain | 0.3.1 |
| LLM Client | langchain-openai | 0.2.1 |
| LLM | OpenAI GPT-4o | via API |
| Containerisation | Docker + Compose | — |

---

## 4. Database Schema

### 4.1 Enums

| Enum | Values |
|---|---|
| `CropType` | Sugarcane, Wheat, Rice, Cotton, Maize, Vegetables |
| `RequestStatus` | pending, negotiating, accepted, rejected, completed |
| `SwapStatus` | proposed, accepted, rejected, completed |
| `CreditStatus` | pending, active, redeemed, expired |
| `NotificationChannel` | chat, sms, ivr, print |

### 4.2 Farmer

Primary table for all registered canal users.

| Field | Type | Description |
|---|---|---|
| `id` | int (PK) | Auto-increment primary key |
| `farmer_id` | str (unique) | Human ID e.g. "F001" |
| `name` | str | Full name |
| `phone` | str | Mobile number |
| `plot_number` | str (unique) | e.g. "Plot-1" |
| `canal_position` | int | 1 = most upstream, 6 = most downstream |
| `crop_type` | CropType | Type of crop grown |
| `flow_efficiency_index` | float | η — usable water ratio (0.0–1.0) |
| `water_credit_balance` | float | Accumulated compensated hours |
| `total_hours_allocated` | float | Lifetime scheduled hours |
| `total_hours_used` | float | Lifetime actual irrigation hours |
| `historical_deficit` | float | Cumulative unmet water hours |
| `missed_turns` | int | Number of skipped irrigation slots |
| `created_at` | datetime | Record creation timestamp |

### 4.3 IrrigationSchedule

One row per scheduled water slot.

| Field | Type | Description |
|---|---|---|
| `id` | int (PK) | Auto-increment |
| `farmer_id` | int (FK → farmer) | Owner of this slot |
| `slot_start` | datetime | Irrigation start time |
| `slot_end` | datetime | Irrigation end time |
| `hours_allocated` | float | Planned irrigation hours |
| `hours_used` | float | Actual hours consumed |
| `status` | str | scheduled / active / completed / swapped |
| `notes` | str (nullable) | E.g. "Yielded to Farukh — emergency swap" |
| `created_at` | datetime | Record creation timestamp |

### 4.4 EmergencyRequest

Stores every incoming emergency request and its resolution.

| Field | Type | Description |
|---|---|---|
| `id` | int (PK) | Auto-increment |
| `farmer_id` | int (FK → farmer) | Requesting farmer |
| `raw_message` | str | Original free-text message |
| `extracted_crop` | str (nullable) | Parsed crop type |
| `extracted_urgency` | str (nullable) | low / medium / high / critical |
| `extracted_hours` | float (nullable) | Requested hours |
| `extracted_plot` | str (nullable) | Plot number if mentioned |
| `status` | RequestStatus | Current resolution status |
| `fwos_score` | float (nullable) | Computed Fair Water Opportunity Score |
| `resolution_summary` | str (nullable) | Consent reason or outcome |
| `decision_trace` | str (nullable) | JSON-serialised agent_steps array |
| `created_at` | datetime | Submission time |
| `updated_at` | datetime | Last status change |

### 4.5 NegotiationRecord

One row per completed negotiation attempt.

| Field | Type | Description |
|---|---|---|
| `id` | int (PK) | Auto-increment |
| `emergency_request_id` | int (FK) | Linked emergency request |
| `requesting_farmer_id` | int (FK) | Farmer who needs water |
| `yielding_farmer_id` | int (FK) | Farmer who yields their slot |
| `hours_requested` | float | Hours the requester needs |
| `hours_yielded` | float | Hours the yielding farmer gives |
| `compensation_hours` | float | Calculated hours owed back |
| `yielding_farmer_eta` | float | η of the yielding farmer |
| `receiving_farmer_eta` | float | η of the requesting farmer |
| `proposal_text` | str | Full swap proposal text |
| `status` | SwapStatus | Current swap status |
| `agent_steps` | str (nullable) | JSON array of all 6 agent outputs |
| `created_at` | datetime | Negotiation timestamp |
| `updated_at` | datetime | Last update |

### 4.6 WaterCredit

Issued when a farmer yields their slot. Redeemable for future irrigation.

| Field | Type | Description |
|---|---|---|
| `id` | int (PK) | Auto-increment |
| `credit_id` | str (unique) | E.g. "CR-A1B2C3D4" |
| `giving_farmer_id` | int (FK) | Farmer who owes hours back |
| `receiving_farmer_id` | int (FK) | Farmer who earned the credit |
| `negotiation_id` | int (FK) | Source negotiation |
| `hours_given` | float | Actual hours yielded |
| `hours_owed` | float | Compensated hours to return |
| `status` | CreditStatus | active / redeemed / expired |
| `notes` | str (nullable) | Context note |
| `created_at` | datetime | Issue timestamp |
| `redeemed_at` | datetime (nullable) | When redeemed |

### 4.7 NotificationLog

Tracks every outbound message per channel.

| Field | Type | Description |
|---|---|---|
| `id` | int (PK) | Auto-increment |
| `farmer_id` | int (FK) | Recipient farmer |
| `negotiation_id` | int (FK) | Related negotiation |
| `channel` | NotificationChannel | chat / sms / ivr / print |
| `message_text` | str | Full message content |
| `sent_at` | datetime | Dispatch timestamp |
| `delivered` | bool | Delivery confirmation flag |

### 4.8 AuditLog

Append-only immutable record of every system action.

| Field | Type | Description |
|---|---|---|
| `id` | int (PK) | Auto-increment |
| `event_type` | str | swap_accepted / credit_issued / schedule_changed / system_seed |
| `actor` | str | Agent name or farmer ID |
| `description` | str | Human-readable action description |
| `metadata_json` | str (nullable) | JSON with IDs, amounts, context |
| `timestamp` | datetime | Event time (never updated) |

---

## 5. Seed Data — Demo Farmers

Six farmers are automatically loaded on first server start, representing a complete upstream-to-downstream canal.

| ID | Name | Plot | Position | Crop | η | Deficit | Missed |
|---|---|---|---|---|---|---|---|
| F001 | Arjun Patil | Plot-1 | 1 (upstream) | Wheat | 1.00 | 0.0 hrs | 0 |
| F002 | Bharat Sharma | Plot-2 | 2 | Rice | 0.95 | 0.5 hrs | 0 |
| F003 | Chandrakant Desai | Plot-3 | 3 | Cotton | 0.88 | 0.8 hrs | 1 |
| F004 | Dinesh Kumar | Plot-4 | 4 | Maize | 0.80 | 1.2 hrs | 1 |
| F005 | Eknath Jadhav | Plot-5 | 5 | Vegetables | 0.72 | 1.8 hrs | 2 |
| F006 | Farukh Mirza | Plot-6 | 6 (downstream) | Sugarcane | 0.65 | 2.5 hrs | 3 |

Each farmer gets one 3-hour irrigation slot the following day, assigned in order (06:00–09:00, 09:00–12:00, …, 21:00–00:00).

A pre-existing credit is also seeded: Plot-3 yielded 1.5 hrs to Plot-5 → Plot-5 owes back 1.88 hrs (`1.5 × 0.88 / 0.72`).

---

## 6. The Core Problem Solved

Traditional canal systems assign water **by time** — each farmer gets 3 hours in rotation. This is unfair because:

- Upstream farmers (position 1–2) receive **full flow** — their 3 hours delivers 3 hours of effective water.
- Downstream farmers (position 5–6) receive **reduced flow** due to seepage, evaporation, and upstream extraction — their 3 hours may deliver only 1.95 hours of effective water (η = 0.65).

NeerSetu solves this by:

1. **Measuring usable water opportunity**, not clock time (via η).
2. **Scoring urgency fairly** using FWOS — downstream farmers score higher, justifying priority.
3. **Compensating yielding farmers** with more hours than they gave, calculated via the η ratio.
4. **Recording everything** so no dispute can arise over what was agreed.

---

## 7. FWOS — Fair Water Opportunity Score

FWOS is a 0–100 score computed for every emergency request. Higher score = higher priority = stronger claim for immediate water.

### Formula

```
FWOS = Downstream Penalty
     + Efficiency Deficit
     + Historical Deficit Score
     + Missed Turns Score
     + Crop Urgency Score
```

### Components

| Component | Formula | Max Points | Meaning |
|---|---|---|---|
| Downstream Penalty | `(canal_position − 1) / (max_position − 1) × 30` | 30 | Further downstream = higher score |
| Efficiency Deficit | `(1 − η) × 20` | 20 | Lower flow efficiency = higher score |
| Historical Deficit | `min(deficit / 5.0, 1.0) × 25` | 25 | More unmet hours in history = higher score |
| Missed Turns | `min(missed_turns / 5.0, 1.0) × 15` | 15 | More missed slots = higher score |
| Crop Urgency | `urgency_weight × 10` | 10 | critical=1.0, high=0.75, medium=0.5, low=0.25 |
| **TOTAL** | | **100** | |

### Example — Farukh Mirza (Plot-6, F006)

```
Canal position:     6  →  (6−1)/(6−1) × 30  = 30.00
η = 0.65            →  (1−0.65) × 20       =  7.00
Historical deficit: 2.5 hrs → (2.5/5.0) × 25  = 12.50
Missed turns:       3   →  (3/5) × 15         =  9.00
Urgency: critical   →  1.0 × 10               = 10.00
                                          ────────────
FWOS                                     = 68.50
```

A score of 68+ triggers automatic consent approval.

### Urgency Weight Table

| Urgency | Weight | Example trigger words |
|---|---|---|
| critical | 1.0 | "dying", "drying", "drought" |
| high | 0.75 | "emergency", "urgent", "today" |
| medium | 0.5 | "need", "soon" |
| low | 0.25 | "request" |

---

## 8. Compensation Formula

When a farmer yields their slot, they receive back **more hours than they gave**, because the receiving farmer's lower η means those hours are worth less to them.

```
Compensated Hours = Yielded Hours × (Yielding η / Receiving η)
```

### Example

```
Yielding farmer:  Arjun Patil, η = 1.00 (Plot-1, upstream)
Receiving farmer: Farukh Mirza, η = 0.65 (Plot-6, downstream)
Hours yielded:    2.0 hrs

Compensation = 2.0 × (1.00 / 0.65) = 3.08 hrs
```

Arjun gives 2 hours of full-flow water and gets back 3.08 hours. This accounts for the fact that Farukh's 3.08 hours at 65% efficiency equals roughly the same amount of actual water as Arjun's 2 hours at 100% efficiency.

The formula is implemented identically in both Python (`negotiation_agent.py`) and TypeScript (`fairness.ts`) for consistent display.

---

## 9. The 6-Agent LangGraph Pipeline

Each agent is a pure function: `NeerSetuState → NeerSetuState`. They share a single `NeerSetuState` TypedDict that is passed through the graph and enriched at each step.

### Agent 1 — Intake Agent

**File:** `backend/agents/intake_agent.py`

**Purpose:** Parse the farmer's free-text emergency message into structured data.

**Input from state:**
- `raw_message` — e.g. "My sugarcane is drying. I need 3 hours today."
- `farmer_name` — from DB

**Processing:**
1. If `OPENAI_API_KEY` is set: sends message to GPT-4o with a system prompt requesting JSON output with `extracted_crop`, `extracted_urgency`, `extracted_hours`, `extracted_plot`.
2. If no key or LLM fails: runs rule-based keyword extraction.
   - Crop detection: matches keywords (`sugarcane`, `wheat`, `rice`, `paddy`, `cotton`, `maize`, `corn`, `vegetables`, `onion`, `tomato`)
   - Urgency detection: matches keywords (`dying/drying/drought` → critical, `emergency/urgent/today` → high, `soon/need` → medium, `request` → low)
   - Hours: regex `(\d+(?:\.\d+)?)\s*(?:hours?|hrs?)`, defaults to 3.0
   - Plot: regex `plot[- ]?(\d+)`

**Output to state:**
- `extracted_crop`, `extracted_urgency`, `extracted_hours`, `extracted_plot`

---

### Agent 2 — Flow & Fairness Agent

**File:** `backend/agents/fairness_agent.py`

**Purpose:** Compute the FWOS and generate a human-readable explanation.

**Input from state:**
- `canal_position`, `flow_efficiency_index`, `historical_deficit`, `missed_turns`, `extracted_urgency`

**Processing:**
1. Runs `compute_fwos()` with the 5-component formula (see Section 7).
2. Calls `build_explanation()` to produce a plain-language justification string like:
   ```
   "Plot-6 received priority because:
   • Downstream position #6 detected — penalty applied
   • Flow Efficiency Index (η) = 0.65
   • Historical water deficit = 2.5 hours
   • Crop urgency: Sugarcane rated critical
   • Missed turns factor included

   FWOS = 68.5"
   ```

**Output to state:**
- `fwos_score`, `fwos_breakdown` (dict with all 5 component values), `fairness_explanation`

---

### Agent 3 — Negotiation Agent

**File:** `backend/agents/negotiation_agent.py`

**Purpose:** Identify the yielding farmer and compute the compensation deal.

**Input from state:**
- `db_yielding_farmer_data` — injected by the API before pipeline runs (see `emergency.py`)
- `extracted_hours`, `flow_efficiency_index`

**Yielding farmer selection logic** (in `emergency.py`, before pipeline):
1. Query all farmers upstream of the requesting farmer (`canal_position < requester.canal_position`), ordered closest-first.
2. Pick the first one who has a `scheduled` slot.
3. Fallback: any upstream farmer.

**Processing:**
1. Caps hours_yielded at `min(requested, 3.0)`.
2. Calls `compute_compensation(hours_yielded, yielding_eta, receiving_eta)`.
3. If LLM available: generates a 3-4 sentence proposal via GPT-4o.
4. Fallback: generates structured template proposal.

**Output to state:**
- `yielding_farmer_id`, `yielding_farmer_name`, `yielding_farmer_eta`
- `hours_yielded`, `compensation_hours`, `proposal_text`

---

### Agent 4 — Consent Agent

**File:** `backend/agents/consent_agent.py`

**Purpose:** Simulate or process the yielding farmer's consent.

**Input from state:**
- `fwos_score`, `extracted_urgency`, `compensation_hours`, `hours_yielded`, `proposal_text`

**Processing:**
1. If LLM available: sends proposal to GPT-4o asking it to simulate a realistic farmer response. Returns `{"decision": "accepted"/"rejected", "reason": "..."}`.
2. Rule-based fallback:
   - If FWOS ≥ 70 OR urgency == critical → **accepted**
   - If FWOS ≥ 50 AND compensation > hours_yielded → **accepted**
   - Otherwise → **accepted** (default — can be tuned for production)
3. If rejected, generates 3 alternative proposals.

**Output to state:**
- `consent_decision` ("accepted" / "rejected")
- `consent_reason`
- `alternative_proposals` (only if rejected)

---

### Agent 5 — Ledger Agent

**File:** `backend/agents/ledger_agent.py`

**Purpose:** Commit all changes to the database atomically.

**Input from state:**
- `consent_decision`, `farmer_id`, `yielding_farmer_id`
- All swap details, compensation values, agent_steps

**Processing (only if consent == "accepted"):**
1. Generates unique `credit_id` = `CR-` + 8 hex chars (uppercase).
2. Opens a DB session and in a single transaction:
   - Creates a `WaterCredit` record (giving_farmer = requester who owes back, receiving_farmer = yielding farmer who earned credit).
   - Increments `yielding_farmer.water_credit_balance` by `compensation_hours`.
   - Creates a `NegotiationRecord` with full agent_steps JSON.
   - Marks the yielding farmer's nearest scheduled slot as `"swapped"`.
   - Updates the `EmergencyRequest` status to `accepted` and stores the full `decision_trace`.
   - Writes 2 immutable `AuditLog` entries: `swap_accepted` and `credit_issued`.
3. Commits the transaction.

**Output to state:**
- `credit_id`, `ledger_updated=True`, `schedule_updated=True`

---

### Agent 6 — Dispatcher Agent

**File:** `backend/agents/dispatcher_agent.py`

**Purpose:** Generate all four notification formats.

**Input from state:** All fields from previous agents.

**Generates:**

**Chat notification** — Rich markdown message with emojis, FWOS score, swap details, credit ID, and the full fairness explanation.

**SMS notification** — Stripped to ≤160 characters:
```
NEERSETU: Swap APPROVED. Arjun Patil yields 2.0h to Farukh Mirza.
Credit 3.08h issued (#CR-A1B2C3D4). Water starts soon.
```

**IVR script** — Spoken-word script with timed pauses:
```
GREETING: "Namaste. This is NeerSetu, your canal coordination system."
[PAUSE 1 second]
ANNOUNCEMENT: "An emergency irrigation swap has been approved."
...
```

**Printable schedule** — Plain-text ASCII table of all farmer slots with SWAPPED/EMERGENCY markers.

**Output to state:**
- `chat_notification`, `sms_notification`, `ivr_script`, `print_schedule`
- `completed = True`

---

## 10. Pipeline Graph Structure

```
START
  │
  ▼
[intake] ──────────────────────────────────────────────────────
  │
  ▼
[fairness] ─────────────────────────────────────────────────────
  │
  ▼
[negotiation]
  │
  ├─── (error: no yielding farmer found) ──────────────────────┐
  │                                                            │
  ▼                                                            │
[consent]                                                      │
  │                                                            │
  ▼                                                            │
[ledger]                                                       │
  │                                                            │
  ▼                                                            ▼
[dispatcher] ◄──────────────────────────────────────────────────
  │
  ▼
END
```

The only conditional edge is after `negotiation`: if `state["error"]` is set (no upstream farmer available), the pipeline skips consent and ledger and goes directly to dispatcher to generate a rejection notification.

---

## 11. Backend API Routes

Base URL: `http://localhost:8000`

### Dashboard

| Method | Path | Description |
|---|---|---|
| GET | `/dashboard/` | Returns full dashboard data: summary stats, farmer cards with FWOS, upcoming schedule, canal flow percentages, active emergency requests |

### Farmers

| Method | Path | Description |
|---|---|---|
| GET | `/farmers/` | List all farmers ordered by canal position |
| GET | `/farmers/{farmer_id}` | Single farmer by string ID (e.g. "F006") |
| POST | `/farmers/` | Create a new farmer |
| PATCH | `/farmers/{farmer_id}` | Update credit balance, deficit, missed turns, or η |
| GET | `/farmers/{farmer_id}/stats` | Efficiency ratio and usage stats |

### Schedules

| Method | Path | Description |
|---|---|---|
| GET | `/schedules/` | All schedules ordered by slot_start |
| GET | `/schedules/active` | Currently active slot, or next upcoming |
| POST | `/schedules/` | Create a new schedule slot |

### Emergency Requests

| Method | Path | Description |
|---|---|---|
| GET | `/emergency/` | All emergency requests, newest first |
| GET | `/emergency/{request_id}` | Single request by ID |
| POST | `/emergency/process` | **Main pipeline endpoint** — runs all 6 agents, returns full `PipelineResponse` |

**POST /emergency/process — Request body:**
```json
{
  "farmer_id": "F006",
  "raw_message": "My sugarcane is drying. I need 3 hours today urgently."
}
```

**POST /emergency/process — Response (PipelineResponse):**
```json
{
  "emergency_request_id": 1,
  "status": "accepted",
  "fwos_score": 68.5,
  "consent_decision": "accepted",
  "consent_reason": "High FWOS (68) confirms genuine downstream disadvantage...",
  "proposal_text": "SWAP PROPOSAL\n...",
  "chat_notification": "✅ *NeerSetu Swap Confirmed*\n...",
  "sms_notification": "NEERSETU: Swap APPROVED...",
  "ivr_script": "[NeerSetu IVR Script]\n...",
  "print_schedule": "═══════ NEERSETU IRRIGATION SCHEDULE ═══════\n...",
  "fairness_explanation": "\"Plot-6 received priority because:\n...",
  "credit_id": "CR-A1B2C3D4",
  "compensation_hours": 3.08,
  "hours_yielded": 2.0,
  "yielding_farmer_name": "Arjun Patil",
  "fwos_breakdown": {
    "downstream_penalty": 30.0,
    "efficiency_deficit": 7.0,
    "historical_deficit_score": 12.5,
    "missed_turns_score": 9.0,
    "crop_urgency_score": 10.0,
    "total": 68.5
  },
  "agent_steps": [
    { "agent": "Intake Agent", "status": "complete", "output": "...", "details": {} },
    { "agent": "Flow & Fairness Agent", "status": "complete", "output": "...", "details": {} },
    ...
  ]
}
```

### Negotiations

| Method | Path | Description |
|---|---|---|
| GET | `/negotiations/` | All negotiation records with farmer names |
| GET | `/negotiations/{id}` | Single negotiation with full agent_steps |

### Water Credits

| Method | Path | Description |
|---|---|---|
| GET | `/credits/` | All credits with farmer names |
| GET | `/credits/farmer/{farmer_id}` | Credits for a specific farmer |
| GET | `/credits/summary` | Aggregate stats (totals, active count, net compensation) |
| PATCH | `/credits/{credit_id}/redeem` | Mark a credit as redeemed |

### Audit Log

| Method | Path | Description |
|---|---|---|
| GET | `/audit/` | Last N audit entries (default 50), newest first |
| GET | `/audit/stats` | Total events and breakdown by event_type |

---

## 12. Frontend Pages

### 12.1 Dashboard (`/dashboard`)

**API call:** `GET /dashboard/`

**What it shows:**
- 4 summary stat cards: Total Farmers, Active Emergencies, Active Credits, Hours Owed
- Upcoming irrigation schedule with farmer name, slot time, flow badge (η), and status
- Canal Flow Efficiency bar chart (one bar per plot, coloured by η)
- FWOS score cards for all 6 farmers with colour-coded scores (red = urgent, green = low priority)
- Recharts BarChart comparing Flow Efficiency % vs FWOS score
- Alert banner if any emergency requests are pending

### 12.2 Farmers (`/farmers`)

**API call:** `GET /farmers/`

**What it shows:**
- Grid of 6 farmer cards, one per plot
- Each card: farmer ID badge, name, plot, canal position, crop type, η badge, FWOS score
- Flow efficiency bar (animated)
- Mini stats: credit balance, historical deficit, missed turns
- Expand toggle reveals: phone, hours allocated/used, efficiency ratio, full FWOS breakdown with 5 component bars

### 12.3 Emergency Request (`/emergency`)

**API calls:** `GET /farmers/`, `GET /emergency/`, `POST /emergency/process`

**What it shows:**
- Dropdown to select farmer
- Quick demo message buttons (3 preset messages)
- Free-text textarea
- "Run Pipeline" button — submits to `POST /emergency/process`
- On result:
  - Green/red status banner with consent decision
  - FWOS score (large number)
  - Swap details: yielding farmer, hours yielded, compensation hours
  - η-adjusted compensation formula displayed visually
  - AI Decision Explanation card (the fairness_explanation text)
  - 4 notification channel toggle buttons: Chat, SMS, IVR, Print
  - Each shows the actual generated notification text
- Past requests list at the bottom

### 12.4 Agent Negotiation (`/negotiation`)

**API call:** `GET /negotiations/`

**What it shows:**
- Expandable cards for each negotiation
- Header: requesting farmer → yielding farmer, swap amount badge, status
- Expanded view:
  - Swap details table (hours requested, yielded, compensation formula)
  - Proposal text in a purple card
  - Full agent decision trace timeline — one entry per agent with coloured icon, status icon (✓/✗/⟳), output text, and key/value detail pairs

### 12.5 Canal Simulation (`/canal`)

**API call:** `GET /dashboard/`

**What it shows:**
- Animated canal visualisation: a source box, a horizontal flow pipe, 6 plot branches below
- "Simulate Flow" button triggers a water blob animation moving left to right, lighting up each plot as water arrives
- Each plot card shows: plot name, farmer first name, η value, coloured flow bar
- Colour coding: green (η ≥ 0.9), yellow (η ≥ 0.8), orange (η ≥ 0.7), red (η < 0.7)
- Flow Efficiency by Position — horizontal bar chart for all 6 plots
- Explanatory panel: why flow decreases downstream (seepage, evaporation, upstream extraction, head losses) and how NeerSetu compensates

### 12.6 Water Credits (`/credits`)

**API calls:** `GET /credits/`, `GET /credits/summary`, `GET /audit/`

**What it shows:**
- 4 summary cards: Total Credits, Active, Hours Given, Hours Owed
- Tab switcher: "Water Credits" / "Audit Log"
- Credits tab: table of all credits with giving/receiving farmer, hours_given ↔ hours_owed, status badge, "Redeem" button
- Audit Log tab: append-only list with event_type badge, description, actor, timestamp

---

## 13. Notification Channels

Every resolved emergency generates 4 notification formats simultaneously.

### Chat (rich markdown)
```
✅ *NeerSetu Swap Confirmed*

🌾 *Emergency Request Resolved*
Farmer: Farukh Mirza | Plot-6 | Crop: Sugarcane
Fair Water Opportunity Score: *68.5/100*

💧 *Swap Details:*
• Arjun Patil yields *2.0 hours* now
• Farukh Mirza receives water immediately
• Arjun Patil earns *3.08 hours* credit (Water Credit #CR-A1B2C3D4)

📋 *Decision Basis:*
"Plot-6 received priority because:
• Downstream position #6 detected...
FWOS = 68.5"

_All parties have been notified. Ledger updated._
```

### SMS (≤160 characters)
```
NEERSETU: Swap APPROVED. Arjun Patil yields 2.0h to Farukh Mirza.
Credit 3.08h issued (#CR-A1B2C3D4). Water starts soon.
```

### IVR Script
```
[NeerSetu IVR Script]
GREETING: "Namaste. This is NeerSetu, your canal coordination system."
[PAUSE 1 second]
ANNOUNCEMENT: "An emergency irrigation swap has been approved."
[PAUSE 0.5 seconds]
DETAILS: "Farmer Farukh Mirza has been granted 2.0 hours of water immediately."
[PAUSE 0.5 seconds]
"Farmer Arjun Patil has yielded their slot and will receive 3.08 compensated hours."
CREDIT: "Water credit number CR-A1B2C3D4 has been issued to Arjun Patil."
CLOSING: "Thank you for cooperating with NeerSetu's fair water distribution system."
"For assistance, press 1. To hear this again, press 2."
```

### Printable Schedule
```
═══════════════════════════════════════════════════════
           NEERSETU IRRIGATION SCHEDULE
           Date: 02 October 2026
═══════════════════════════════════════════════════════
ID     Farmer               Plot     Crop         Slot           Status
───────────────────────────────────────────────────────
F001   Arjun Patil          Plot-1   Wheat        06:00–09:00    ⚡ SWAPPED
F002   Bharat Sharma        Plot-2   Rice         09:00–12:00    ✓ Scheduled
F003   Chandrakant Desai    Plot-3   Cotton       12:00–15:00    ✓ Scheduled
F004   Dinesh Kumar         Plot-4   Maize        15:00–18:00    ✓ Scheduled
F005   Eknath Jadhav        Plot-5   Vegetables   18:00–21:00    ✓ Scheduled
F006   Farukh Mirza         Plot-6   Sugarcane    EMERGENCY      ⚡ ACTIVE
───────────────────────────────────────────────────────
Emergency swap approved. Credit #CR-A1B2C3D4 issued.
═══════════════════════════════════════════════════════
```

---

## 14. Water Credit System

The credit system is the backbone of NeerSetu's fairness guarantee.

### How a credit is created

1. A swap is approved (consent = accepted).
2. The Ledger Agent generates `credit_id = "CR-" + 8 random uppercase hex chars`.
3. A `WaterCredit` row is written:
   - `giving_farmer_id` = requesting farmer (they owe hours back)
   - `receiving_farmer_id` = yielding farmer (they earned hours)
   - `hours_given` = actual hours yielded (e.g. 2.0)
   - `hours_owed` = compensated hours (e.g. 3.08)
   - `status` = active
4. The yielding farmer's `water_credit_balance` field is incremented by `compensation_hours`.

### How a credit is redeemed

- `PATCH /credits/{credit_id}/redeem`
- Sets `status = redeemed`, sets `redeemed_at = now()`.
- Decrements the receiving farmer's `water_credit_balance` by `hours_owed`.

### Why credits are η-adjusted

The receiving farmer (who yielded) is in a more efficient upstream position. When they later redeem their 3.08 hours, they will receive more effective water than what they gave up. This is intentional — it compensates for the risk and generosity of yielding ahead of schedule.

---

## 15. Audit Log

The `AuditLog` table is append-only by design. No row is ever updated or deleted. Every significant action writes a new entry:

| Event Type | Trigger | Example description |
|---|---|---|
| `system_seed` | Server start | "Database seeded with 6 demo farmers and initial schedules." |
| `swap_accepted` | Ledger Agent | "Swap: Arjun Patil yields 2.0 hrs to Farukh Mirza" |
| `credit_issued` | Ledger Agent | "Credit CR-A1B2C3D4: 3.08 hrs owed to Arjun Patil" |

The `metadata_json` field stores relevant IDs for traceability:
```json
{"credit_id": "CR-A1B2C3D4", "negotiation_id": 1}
```

---

## 16. How a Request Flows End-to-End

Step-by-step walkthrough of the demo scenario:

**Input:**
- Farmer: F006 — Farukh Mirza (Plot-6, η=0.65, downstream)
- Message: "My sugarcane is drying. I need 3 hours of water today urgently."

**Step 1 — API receives request (`POST /emergency/process`)**
- Resolves F006 from DB
- Queries for best yielding farmer → finds F005 (Eknath Jadhav, closest upstream with a scheduled slot)
- Creates EmergencyRequest row (status = negotiating)
- Builds initial state dict with all farmer fields
- Calls `neersetu_pipeline.invoke(initial_state)`

**Step 2 — Intake Agent**
- Detects "drying" → urgency = critical
- Detects "sugarcane" → crop = Sugarcane
- Detects "3 hours" → extracted_hours = 3.0

**Step 3 — Flow & Fairness Agent**
- canal_position=6, η=0.65, deficit=2.5, missed=3, urgency=critical
- FWOS = 30 + 7 + 12.5 + 9 + 10 = **68.5**
- Generates explanation string

**Step 4 — Negotiation Agent**
- Yielding farmer: Eknath Jadhav (η=0.72)
- hours_yielded = min(3.0, 3.0) = 3.0
- compensation = 3.0 × (0.72 / 0.65) = **3.32 hrs**
- Generates proposal text

**Step 5 — Consent Agent**
- FWOS = 68.5 ≥ 70? No. Urgency = critical? Yes → **accepted**
- Reason: "High FWOS confirms genuine downstream disadvantage."

**Step 6 — Ledger Agent**
- Creates WaterCredit: CR-XXXXXXXX, hours_given=3.0, hours_owed=3.32
- Creates NegotiationRecord with all agent_steps serialised
- Marks Eknath's schedule slot as "swapped"
- Updates EmergencyRequest to "accepted"
- Writes 2 AuditLog entries

**Step 7 — Dispatcher Agent**
- Generates Chat, SMS, IVR, Print notifications
- Sets completed=True

**Step 8 — API returns PipelineResponse**
- All 6 agent outputs, notifications, credit ID, FWOS breakdown returned in one JSON response
- Frontend renders the result immediately

---

## 17. Without an OpenAI Key

Every agent has a fully functional deterministic fallback:

| Agent | Without API key |
|---|---|
| Intake | Keyword regex extraction |
| Fairness | Pure formula (no LLM needed at all) |
| Negotiation | Template-based proposal text |
| Consent | Rule-based (FWOS ≥ 70 or urgency=critical → accept) |
| Ledger | DB operations (no LLM involved) |
| Dispatcher | Template-based notification generation |

To enable LLM mode, add `OPENAI_API_KEY=sk-...` to `backend/.env`.

---

## 18. File Structure

```
neersetu/
│
├── README.md               Project overview
├── RUN.md                  Setup commands for any machine
├── REPORT.md               This file
│
├── backend/
│   ├── main.py             FastAPI app entry, CORS, lifespan (init_db + seed)
│   ├── requirements.txt    Python dependencies
│   ├── .env.example        Environment variable template
│   │
│   ├── models/
│   │   └── models.py       All SQLModel table definitions + enums
│   │
│   ├── db/
│   │   ├── database.py     SQLite engine, Session factory, init_db()
│   │   └── seed.py         Demo data loader (6 farmers, schedules, 1 credit)
│   │
│   ├── agents/
│   │   ├── state.py        NeerSetuState TypedDict + AgentStep TypedDict
│   │   ├── llm.py          ChatOpenAI singleton factory
│   │   ├── intake_agent.py     Agent 1: parse free-text message
│   │   ├── fairness_agent.py   Agent 2: compute FWOS
│   │   ├── negotiation_agent.py Agent 3: select yielding farmer + compensation
│   │   ├── consent_agent.py    Agent 4: simulate/process consent
│   │   ├── ledger_agent.py     Agent 5: DB writes + audit
│   │   ├── dispatcher_agent.py Agent 6: generate notifications
│   │   └── pipeline.py         LangGraph StateGraph definition + singleton
│   │
│   └── api/
│       ├── dashboard.py    GET /dashboard/ (aggregated home page data)
│       ├── farmers.py      CRUD for /farmers/
│       ├── schedules.py    CRUD for /schedules/
│       ├── emergency.py    GET+POST /emergency/ — main pipeline trigger
│       ├── negotiations.py GET /negotiations/
│       ├── credits.py      GET+PATCH /credits/
│       └── audit.py        GET /audit/
│
├── frontend/
│   ├── package.json
│   ├── next.config.ts      Rewrites: /api/* → localhost:8000/*
│   ├── tailwind.config.ts  Custom colours: water (blue), farm (green), soil (amber)
│   ├── tsconfig.json
│   │
│   └── src/
│       ├── app/
│       │   ├── layout.tsx          Root layout with Sidebar + TopBar
│       │   ├── page.tsx            Redirects / → /dashboard
│       │   ├── globals.css         Tailwind base + custom card/btn/badge classes
│       │   ├── dashboard/page.tsx  Dashboard page
│       │   ├── farmers/page.tsx    Farmers grid page
│       │   ├── emergency/page.tsx  Emergency request + pipeline result page
│       │   ├── negotiation/page.tsx Agent trace timeline page
│       │   ├── canal/page.tsx      Animated canal simulation page
│       │   └── credits/page.tsx    Credits ledger + audit log page
│       │
│       ├── components/
│       │   └── layout/
│       │       ├── Sidebar.tsx     Left nav with route links
│       │       └── TopBar.tsx      Page title + system status indicator
│       │
│       ├── lib/
│       │   ├── api.ts          All axios calls to backend endpoints
│       │   ├── utils.ts        cn(), formatHours(), urgencyColor(), statusColor(), fwosColor()
│       │   └── fairness.ts     Client-side FWOS + compensation formula (mirrors Python)
│       │
│       └── types/
│           └── index.ts        TypeScript interfaces for all API response shapes
│
└── docker/
    ├── Dockerfile.backend      Python 3.12-slim, installs deps, seeds DB, starts uvicorn
    ├── Dockerfile.frontend     Node 20 multi-stage build, Next.js standalone output
    └── docker-compose.yml      Backend + frontend services, health checks, volume
```

---

*NeerSetu — Built by ThinkByte*
