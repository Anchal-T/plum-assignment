# Plum OPD Claim Adjudication Tool

AI-powered system that automates the adjudication of Outpatient Department (OPD) insurance claims by processing medical documents, extracting information via LLMs, and making approval/rejection decisions against policy rules.

## Architecture

```
frontend/       React + TypeScript + Vite (deployed on Vercel)
backend/        FastAPI + Python (deployed on Vercel serverless)
database/       Supabase (PostgreSQL)
llm/            Google Gemini 3.5 Flash for document extraction
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite |
| Backend | Python 3.12, FastAPI |
| Database | Supabase (PostgreSQL) |
| LLM | Google Gemini 3.5 Flash |
| Auth | Supabase Row Level Security |
| Deployment | Vercel (multi-service) |

## Project Structure

```
plum/
├── frontend/                  # React SPA
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Route pages
│   │   ├── services/          # API client
│   │   └── types/             # TypeScript types
│   └── ...
├── backend/                   # FastAPI server
│   ├── app/
│   │   ├── api/               # Route handlers
│   │   ├── schemas/           # Pydantic models
│   │   ├── services/          # Business logic
│   │   ├── rules/             # Policy & rule engine
│   │   └── utils/             # Validators & constants
│   ├── supabase/migrations/   # DB migrations
│   └── api/index.py           # Vercel entrypoint
├── vercel.json                # Multi-service config
└── README.md
```

## Setup

### Prerequisites

- Node.js 20+
- Python 3.12+
- [Supabase](https://supabase.com) account
- [Google AI](https://aistudio.google.com) API key

### 1. Clone

```bash
git clone https://github.com/Anchal-T/plum-assignment
cd plum
```

### 2. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

Create `backend/.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
GEMINI_API_KEY=your-gemini-key
```

Run:

```bash
uvicorn app.main:app --reload
```

### 3. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_URL=http://localhost:8000
```

Run:

```bash
npm run dev
```

## API Endpoints

### Claims

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/claims` | Submit a new claim |
| GET | `/api/claims/{id}` | Get claim details |

### Documents

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/documents/process` | Upload & extract document data |

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |

## Decision Engine

The adjudication follows a 5-step pipeline:

1. **Eligibility** — Policy active, waiting periods satisfied
2. **Document Validation** — Legibility, completeness, authenticity
3. **Coverage Verification** — Service covered, not excluded
4. **Limit Validation** — Annual, sub-limit, per-claim limits
5. **Medical Necessity** — Diagnosis justifies treatment

**Outcomes:** `APPROVED` | `REJECTED` | `PARTIAL` | `MANUAL_REVIEW`

## Database Schema

- `members` — Employee/dependent info
- `claims` — Claim submissions
- `documents` — Uploaded documents with OCR data
- `decisions` — Adjudication results
- `audit_logs` — Claim action history

## Deployment

The app uses Vercel multi-service deployment:

```bash
# Deploy both services
git push

# Or deploy manually
vercel deploy
```

Frontend: `https://plum-assignment-five.vercel.app`
Backend: `https://plum-assignment-99an.vercel.app/_/backend`

## Environment Variables

### Backend

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase anon key |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `DEBUG` | No | Enable debug mode |

### Frontend

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend API base URL |
