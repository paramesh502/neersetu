# 💧 NeerSetu — WaterBridge

**Autonomous Multi-Agent Canal Dispatcher and Conflict Resolver**

---

## What Is NeerSetu?

NeerSetu (Hindi: *Neer* = Water, *Setu* = Bridge) is an AI-powered irrigation coordination system for shared canal networks. Unlike traditional time-based schedulers, NeerSetu resolves irrigation disputes through **voluntary compensated exchanges** negotiated by a chain of AI agents.

### Core Innovations

| Feature | Description |
|---|---|
| **Flow-aware fairness** | Hours ≠ usable water. Downstream farmers receive η-adjusted compensation |
| **Agentic negotiation** | 6-agent LangGraph pipeline: Intake → Fairness → Negotiation → Consent → Ledger → Dispatcher |
| **Water credit market** | Every swap issues a tamper-proof credit redeemable for future irrigation hours |
| **Omnichannel dispatch** | Chat, SMS (160-char), IVR script, and printable schedule |
| **Explainable AI** | Every decision includes a human-readable FWOS breakdown |
| **Immutable audit log** | Append-only ledger records every action for accountability |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    NeerSetu System                       │
│                                                         │
│  Frontend (Next.js 15)     Backend (FastAPI)            │
│  ┌──────────────────┐      ┌──────────────────────┐    │
│  │ Dashboard        │◄────►│ /dashboard           │    │
│  │ Farmers          │      │ /farmers             │    │
│  │ Emergency Req.   │      │ /emergency/process   │    │
│  │ Agent Workflow   │      │ /negotiations        │    │
│  │ Canal Simulation │      │ /credits             │    │
│  │ Water Credits    │      │ /audit               │    │
│  └──────────────────┘      └────────┬─────────────┘    │
│                                     │                    │
│                             LangGraph Pipeline           │
│                    ┌────────────────▼──────────────┐    │
│                    │  1. Intake Agent               │    │
│                    │  2. Flow & Fairness Agent      │    │
│                    │  3. Negotiation Agent          │    │
│                    │  4. Consent Agent              │    │
│                    │  5. Ledger Agent               │    │
│                    │  6. Dispatcher Agent           │    │
│                    └───────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Fairness Formula

```
FWOS = Downstream Penalty (30)
     + Efficiency Deficit (20)
     + Historical Deficit (25)
     + Missed Turns (15)
     + Crop Urgency (10)
     ──────────────────────────
     Max = 100
```

**Compensation Formula:**
```
Compensated Hours = Yielded Hours × (Yielding η / Receiving η)

Example:
  Yielded = 2 hrs, η_yielding = 1.0, η_receiving = 0.65
  Compensation = 2 × (1.0 / 0.65) = 3.08 hrs
```

---

## Demo Scenario

Preloaded farmers (6 plots, upstream → downstream):

| Plot | Farmer | Crop | η |
|------|--------|------|---|
| Plot-1 | Arjun Patil | Wheat | 1.00 |
| Plot-2 | Bharat Sharma | Rice | 0.95 |
| Plot-3 | Chandrakant Desai | Cotton | 0.88 |
| Plot-4 | Dinesh Kumar | Maize | 0.80 |
| Plot-5 | Eknath Jadhav | Vegetables | 0.72 |
| Plot-6 | Farukh Mirza | Sugarcane | 0.65 |

**Trigger the demo:**

1. Go to **Emergency Request** page
2. Select Farmer **F006 — Farukh Mirza**
3. Paste: `"My sugarcane is drying. I need 3 hours of water today urgently."`
4. Click **Run Pipeline**

The system will:
1. Parse the request with the Intake Agent
2. Compute FWOS = ~84 (high downstream disadvantage)
3. Find Arjun Patil (Plot-1) as the yielding farmer
4. Propose: Arjun yields 2 hrs → receives 3.08 hrs compensation
5. Consent Agent auto-approves (FWOS > 70)
6. Ledger issues Credit `CR-XXXXXXXX`
7. Dispatch Chat + SMS + IVR + Print notifications

---

## Quick Start

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file and add your OpenAI key (optional — works without it)
cp .env.example .env

# Start server (auto-seeds DB on first run)
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy env file
cp .env.local.example .env.local

# Start dev server
npm run dev
```

App: http://localhost:3000

### Docker (full stack)

```bash
cd docker

# Set your OpenAI API key (optional)
export OPENAI_API_KEY=sk-...

# Build and start
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/dashboard` | Live schedule, FWOS scores, canal flow chart |
| Farmers | `/farmers` | All 6 farmer profiles with FWOS breakdown |
| Emergency Request | `/emergency` | Submit natural-language request, run 6-agent pipeline |
| Agent Negotiation | `/negotiation` | View past negotiations with full agent decision trace |
| Canal Simulation | `/canal` | Animated canal with flow efficiency visualisation |
| Water Credits | `/credits` | Credit ledger + immutable audit log |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 18, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.12 |
| Database | SQLite (via SQLModel) |
| AI Pipeline | LangGraph + LangChain |
| LLM | OpenAI GPT-4o (falls back to rule-based without key) |
| Charts | Recharts |
| Deployment | Docker + Docker Compose |

---

## Without an OpenAI Key

NeerSetu works fully without an API key using deterministic rule-based logic:
- Intake Agent: keyword extraction
- Fairness Agent: formula computation (no LLM needed)
- Negotiation Agent: template-based proposal
- Consent Agent: rule-based (FWOS ≥ 70 → accept)
- Dispatcher Agent: template notifications

Add an `OPENAI_API_KEY` in `.env` to enable richer LLM-generated proposals and IVR scripts.

---

## Project Structure

```
neersetu/
├── backend/
│   ├── agents/          # LangGraph 6-agent pipeline
│   │   ├── state.py
│   │   ├── intake_agent.py
│   │   ├── fairness_agent.py
│   │   ├── negotiation_agent.py
│   │   ├── consent_agent.py
│   │   ├── ledger_agent.py
│   │   ├── dispatcher_agent.py
│   │   └── pipeline.py
│   ├── api/             # FastAPI route handlers
│   ├── db/              # Database + seed data
│   ├── models/          # SQLModel schemas
│   └── main.py
├── frontend/
│   └── src/
│       ├── app/         # Next.js 15 App Router pages
│       ├── components/  # Layout, charts, UI
│       ├── lib/         # API client, utils, fairness
│       └── types/       # TypeScript interfaces
└── docker/              # Dockerfiles + compose
```

---

*Built with ❤️ by ThinkByte*
