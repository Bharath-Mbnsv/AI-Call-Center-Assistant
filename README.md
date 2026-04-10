# AI Call Center Assistant

> Audio or transcript input → structured summary → QA score → review workspace.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Agent Design](#agent-design)
4. [Technology Stack](#technology-stack)
5. [Setup & Installation](#setup--installation)
6. [Usage Guide](#usage-guide)
7. [Project Structure](#project-structure)
8. [Pipeline Deep Dive](#pipeline-deep-dive)
9. [QA Scoring Rubric](#qa-scoring-rubric)
10. [Sample Inputs](#sample-inputs)
11. [API Reference](#api-reference)
12. [Frontend Experience](#frontend-experience)
13. [Testing](#testing)
14. [MCP Server](#mcp-server)
15. [Docker Deployment](#docker-deployment)
16. [Configuration Reference](#configuration-reference)
17. [Design Decisions](#design-decisions)
18. [Troubleshooting](#troubleshooting)
19. [Future Enhancements](#future-enhancements)
20. [Privacy & Compliance](#privacy--compliance)

---

## Overview

In many support teams, useful call insights are buried inside long recordings and inconsistent transcripts. Manual review takes time, summary quality varies, and QA scoring is hard to standardize.

The AI Call Center Assistant automates that workflow with a Python agent pipeline and a React review interface.

**Key capabilities:**

- Accepts transcript text, audio files, or JSON transcript uploads
- Transcribes audio with Whisper when required
- Generates a structured call summary
- Scores interactions across QA dimensions
- Presents results in a React review workspace
- Exposes the pipeline through a FastAPI API and MCP server

**Current UI direction:**

- React frontend instead of the earlier Streamlit UI
- FastAPI backend for analysis endpoints
- Browser-side session history for recent runs

---

## Architecture

### High-Level Data Flow

```text
Input (Transcript, JSON, or Audio)
        │
        ▼
┌────────────────────────────────────────────────────┐
│            LangGraph Pipeline                      │
│                                                    │
│   1. Intake Agent                                  │
│      Validates format and extracts metadata        │
│           │                                        │
│           ▼                                        │
│   2. Conditional Routing                           │
│      Audio -> Transcription Agent                  │
│      Text  -> Text Passthrough                     │
│           │                                        │
│           ▼                                        │
│   3. Summarization Agent                           │
│      Structured summary output                     │
│           │                                        │
│           ▼                                        │
│   4. Quality Scoring Agent                         │
│      Empathy, professionalism, resolution, clarity │
│                                                    │
└────────────────────────────────────────────────────┘
        │
        ▼
FastAPI API
        │
        ▼
React Review Workspace
```

### Workflow Orchestration

1. **Intake** validates the input, extracts metadata, and classifies the input type.
2. **Conditional routing** sends audio to transcription and text to passthrough.
3. **Summarization** produces a structured summary with consistent fields.
4. **QA scoring** evaluates the call across the configured rubric.
5. **Results** are returned to the API and surfaced in the React workspace.

### Application Layers

- `backend/agents` contains the core call-processing logic
- `backend/app` exposes the FastAPI API around that logic
- `frontend` provides the React interface for input, results, and history
- `call_center_mcp` exposes MCP tools/resources for external clients
- `config/mcp.yaml` stores repo-level MCP configuration

---

## Agent Design

| Agent | File | Responsibility |
|------|------|----------------|
| Intake Agent | `backend/agents/intake_agent.py` | Validates input and extracts metadata |
| Transcription Agent | `backend/agents/transcription_agent.py` | Converts audio to text with Whisper |
| Summarization Agent | `backend/agents/summarization_agent.py` | Produces structured summary fields |
| Quality Score Agent | `backend/agents/quality_score_agent.py` | Scores the call with QA dimensions |
| Routing Agent | `backend/agents/routing_agent.py` | Builds and runs the LangGraph pipeline |

### Agent Communication Protocol

Agents do not call each other directly. The router selects the next step based on input type, and all state flows through the pipeline output so the UI and API can stay consistent.

### Structured Outputs

**Summary output includes:**

- one-line summary
- customer issue
- resolution
- action items
- key topics
- sentiment
- call outcome

**QA output includes:**

- empathy
- professionalism
- resolution
- communication clarity
- overall score
- grade
- highlights
- improvements

---

## Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | React + Vite | Review workspace and call analysis UI |
| Backend API | FastAPI | HTTP API for transcript/audio analysis |
| Pipeline | LangGraph | Conditional multi-step orchestration |
| Transcription | OpenAI Whisper (`whisper-1`) | Audio to text |
| Summary + QA | GPT-4o (fallback: GPT-4o-mini) | Structured summary and scoring |
| Validation | Pydantic | Request/response and model validation |
| MCP | FastMCP | External tool/resource access |
| Containerization | Docker + docker-compose | Local full-stack deployment |

---

## Setup & Installation

### Prerequisites

- Python 3.12+
- Node.js 20 or 22 for the Vite frontend
- OpenAI API key

  
### 1. Clone the repository

```bash
git clone https://github.com/Bharath-Mbnsv/AI-Call-Center-Assistant.git
cd AI-Call-Center-Assistant
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Use the provided example:

```bash
cp .env.example .env
```

Add your key:

```env
OPENAI_API_KEY=your_openai_key_here
```

Optional overrides (useful for local CORS or custom API base):

```env
CORS_ORIGINS=http://localhost:5173,http://localhost:8080
VITE_API_BASE_URL=http://localhost:8000/api
```

### 5. Run the application

Backend:

```bash
uvicorn backend.app.main:app --reload
```

The backend runs at `http://localhost:8000`.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at `http://localhost:5173`.

### Node version management (optional)

If you use `nvm`, switch to a supported Node version before running the frontend:

```bash
nvm use 20
```

Or:

```bash
nvm use 22
```

Then start the frontend:

```bash
cd frontend
npm install
npm run dev
```

### Frontend troubleshooting

If frontend install or startup fails because of a Node version mismatch, confirm you are using Node 20 or 22:

```bash
node -v
```

If needed, reinstall frontend dependencies:

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Usage Guide

### Transcript Input

- Paste a full agent/customer transcript into the workspace
- Use speaker turns like `Agent: ...` and `Customer: ...`

### Audio Upload

- Upload `.mp3`, `.mp4`, `.wav`, `.m4a`, `.webm`, or `.ogg`
- Audio is transcribed before scoring

### JSON Transcript

- Accepts `{"transcript": "..."}` or a speaker-turn array
- Example: `[{ "speaker": "Agent", "text": "..." }]`

### Sample Content

- Load built-in sample transcripts from `backend/data/sample_transcripts`

### Run Analysis

- Click **Analyze call** to run intake, transcription, summarization, and QA scoring

---

## Project Structure

```text
AI_Call_Center_Assistant_exp/
├── requirements.txt
├── backend/
│   ├── agents/                 # Pipeline agents
│   ├── app/
│   │   ├── api/                # FastAPI routes and schemas
│   │   ├── services/           # Analysis service layer
│   │   └── main.py             # FastAPI entry point
│   ├── data/
│   │   ├── sample_inputs/      # JSON examples
│   │   └── sample_transcripts/ # Transcript samples
│   ├── tests/
│   │   └── test_all.py         # Backend tests
│   ├── Dockerfile              # Backend container build
│   └── utils/                  # Shared helpers
├── frontend/
│   ├── src/
│   │   ├── app/                # App shell + components
│   │   ├── services/           # API client
│   │   └── shared/             # Types and constants
│   ├── tests/
│   │   ├── api.test.ts         # API client tests
│   │   └── App.test.tsx        # App UI tests
│   ├── nginx.conf              # Frontend runtime config
│   ├── package.json            # Frontend deps/scripts
│   └── Dockerfile              # Frontend container build
├── conftest.py
├── call_center_mcp/
│   └── server.py               # MCP server
├── config/
│   └── mcp.yaml
├── docker-compose.yml
└── .env.example
```

**Backend Tests:**
```text
backend/
└── tests/
    └── test_all.py
```

**Frontend Tests:**
```text
frontend/
└── tests/
    ├── api.test.ts
    └── App.test.tsx
```

---

## Pipeline Deep Dive

### 1. Intake

The intake step validates:

- transcript length
- supported audio file types
- transcript JSON format
- metadata such as call ID and estimated duration

### 2. Transcription

If the input is audio, the transcription agent:

- writes audio bytes to a temporary file
- sends the file to Whisper
- returns transcript text or a structured error

If the input is already text, the pipeline skips transcription.

### 3. Summarization

The summarization agent produces a structured summary with consistent fields for the UI and downstream review.

### 4. QA Scoring

The QA agent evaluates the interaction on the configured rubric and returns:

- per-dimension score
- justification
- overall score
- grade
- strengths and improvements

### Fallback Behavior

The pipeline is designed to continue even if one stage encounters an error.

Errors are:

- collected in the run result
- surfaced in the UI
- marked with `fallback_used`

---

## QA Scoring Rubric

The current scoring dimensions are:

- empathy
- professionalism
- resolution
- communication clarity

Suggested grade interpretation:

- `8-10` Excellent
- `6-7` Good
- `4-5` Needs Improvement
- `<4` Poor

These values are configured in [config/mcp.yaml](/Users/bharathmanda/Downloads/AI_Call_Center_Assistant_exp/config/mcp.yaml).

---

## Sample Inputs

Included samples cover scenarios such as:

- billing disputes
- technical support
- refund requests
- account security
- poor service examples

Locations:

- transcripts: [backend/data/sample_transcripts](/Users/bharathmanda/Downloads/AI_Call_Center_Assistant_exp/backend/data/sample_transcripts)
- sample inputs: [backend/data/sample_inputs](/Users/bharathmanda/Downloads/AI_Call_Center_Assistant_exp/backend/data/sample_inputs)

### Try a Sample

1. Open the **Samples** dropdown in the sidebar.
2. Pick a sample transcript.
3. Click **Analyze call** to run the pipeline.

---

## API Reference

### Health

- `GET /api/health`

### Samples

- `GET /api/samples`
- `GET /api/samples/{slug}`

### Analysis

- `POST /api/analyze/text`
- `POST /api/analyze/json`
- `POST /api/analyze/audio`

### Response Shape

Analysis responses include:

- metadata
- transcript
- summary
- qa_score
- current stage
- errors
- fallback flag

---

## Frontend Experience

The current React UI includes:

- input mode switching
- sample transcript loading
- run-status panel
- summary tab
- quality score tab
- transcript tab
- browser-side session history

Frontend source layout:

- app shell: [frontend/src/app](/Users/bharathmanda/Downloads/AI_Call_Center_Assistant_exp/frontend/src/app)
- API client: [frontend/src/services](/Users/bharathmanda/Downloads/AI_Call_Center_Assistant_exp/frontend/src/services)
- shared types: [frontend/src/shared](/Users/bharathmanda/Downloads/AI_Call_Center_Assistant_exp/frontend/src/shared)

---

## Testing

### Run Backend Tests

```bash
source .venv/bin/activate
pytest backend/tests -q
```

A root [conftest.py](/Users/bharathmanda/Downloads/AI_Call_Center_Assistant_exp/conftest.py) puts the project root on `sys.path` so tests can `import backend.*` and `import call_center_mcp.*` cleanly.

### Run Frontend Tests

```bash
cd frontend
npm install
npm run test    # uses Vitest; requires Node 20 or 22
```

### What Is Covered

- Intake validation
- Summarization and QA score models
- Transcript validation utilities
- MCP helpers and routing behavior
- Sample transcript availability

---

## MCP Server

The MCP server exposes tools and resources for:

- transcript validation
- call summarization
- quality scoring
- full call analysis
- sample transcript access
- config inspection

### Available Tools

- `validate_transcript_input`
- `summarize_call`
- `score_call_quality`
- `analyze_call`
- `get_sample_transcript`

### Available Resources

- `config://mcp-settings`
- `config://runtime-summary`
- `samples://catalog`
- `samples://transcript/{sample_name}`

### Available Prompts

- `supervisor_review`
- `qa_coaching`

### Setup

Run it with:

```bash
python3 call_center_mcp/server.py
```

Or:

```bash
fastmcp run call_center_mcp/server.py
```

Add to Claude Desktop config (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "call-center-assistant": {
      "command": "/absolute_path_to/AI_Call_Center_Assistant_exp/.venv/bin/python",
      "args": ["/absolute_path_to/AI_Call_Center_Assistant_exp/call_center_mcp/server.py"],
      "env": {
        "OPENAI_API_KEY": "your-key-here"
      }
    }
  }
}
```

---

## Docker Deployment

### Prerequisites

- Docker installed and running

### Quick Start

Run the full stack with:

```bash
docker compose up --build
```

### Services

- backend: `http://localhost:8000` (FastAPI/uvicorn, healthcheck on `/api/health`)
- frontend: `http://localhost:8080` (nginx serving the built React app, healthcheck on `/healthz`)

API docs (Docker or local):

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

The frontend container waits for the backend to report healthy before it starts. CORS origins are read from the `CORS_ORIGINS` env var (comma-separated) and default to `http://localhost:8080,http://127.0.0.1:8080` in compose. The frontend's API base URL is baked at build time via the `VITE_API_BASE_URL` build arg.

`docker-compose.yml` stays at the repo root because it orchestrates multiple services.

### Docker Details

- Backend base image: `python:3.12-slim`
- Frontend build image: `node:20-alpine`, runtime image: `nginx:1.27-alpine`
- Health checks: backend `/api/health`, frontend `/healthz`
- Backend image builds from repo root; frontend image builds from `./frontend`

---

## Configuration Reference

### Repo-level config

[config/mcp.yaml](/Users/bharathmanda/Downloads/AI_Call_Center_Assistant_exp/config/mcp.yaml) currently stores:

- primary and fallback model settings
- transcription model and supported formats
- pipeline constraints
- QA rubric thresholds

### Frontend config

Frontend runtime config should be passed with environment variables such as:

- `VITE_API_BASE_URL`

### Backend config

If backend-wide config grows later, it should live under `backend/` in a dedicated config/core area.

---

## Design Decisions

### React Instead of Streamlit

The frontend is now component-based and better aligned with longer-term product polish.

### FastAPI Wrapper Around Existing Agents

The agent pipeline remains reusable instead of being rewritten around the UI.

### MCP Kept Separate

MCP is a parallel interface to the same capabilities, not part of the frontend or API layer.

### Config Centralized at Repo Level

Shared operational config is easier to locate under `config/`.

---

## Troubleshooting

| Problem | Solution |
|---------|----------------|
| Backend import fails | Install backend deps with `pip install -r requirements.txt` |
| Frontend dev server or tests fail | Make sure you are using Node 20 or 22 (Vite 5 / Vitest require it) |
| OpenAI errors | Confirm `OPENAI_API_KEY` is set in `.env` |
| Audio analysis fails | Check format and file size against `config/mcp.yaml` |
| CORS issues locally | Set `CORS_ORIGINS` in `.env` to include the frontend origin (`http://localhost:5173` for `npm run dev`, `http://localhost:8080` under Docker) |

---

## Future Enhancements

- persistent run history
- authentication and user workspaces
- richer QA analytics and charts
- downloadable reports
- queue-based async processing for larger audio uploads
- role-based review workflow for supervisors

---

## Privacy & Compliance

This project is a demo workflow and does not claim production compliance.

Before using it with real customer data, review:

- data retention
- redaction requirements
- PII handling
- audit logging
- vendor and policy requirements

---
