# Run NeerSetu — From Scratch (Any Machine)

## Prerequisites

- Python 3.11+ → https://www.python.org/downloads/
- Node.js 18+ → https://nodejs.org/
- Git → https://git-scm.com/

---

## 1. Clone the repo

```bash
git clone https://github.com/paramesh502/neersetu.git
cd neersetu
```

---

## 2. Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate        # Mac / Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install fastapi==0.115.0 "uvicorn[standard]==0.30.6" sqlmodel==0.0.21 \
  langgraph==0.2.28 langchain==0.3.1 langchain-openai==0.2.1 openai==1.51.0 \
  python-dotenv==1.0.1 httpx==0.27.2 aiofiles==24.1.0 python-multipart==0.0.12

# (Optional) Add OpenAI key for LLM features
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# Start server — auto seeds the database on first run
uvicorn main:app --reload --port 8000
```

---

## 3. Frontend (new terminal tab)

```bash
cd neersetu/frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

---

## 4. Open in browser

| | URL |
|---|---|
| App | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

---

## Demo

1. Go to **Emergency Request** page
2. Select **F006 — Farukh Mirza**
3. Paste: `My sugarcane is drying. I need 3 hours of water today urgently.`
4. Click **Run Pipeline**
