# Construction AI Agents (FastAPI + Frontend Dashboard)

A FastAPI application with a frontend dashboard to manage projects and run AI-assisted agents: material search, cost estimation, advice, report generation, and coordination. Includes authentication, project CRUD, and report export (PDF/JSON).

## Features
- Authentication (login/register, token verification)
- Project management (create, view, update)
- Agents: material-search, estimate, advice, report, coordinate
- Report generation (PDF/JSON) with WeasyPrint
- Frontend dashboard (`static/dashboard.html`) with multi-step project form

## Quickstart

### Prerequisites
- Python 3.10+
- Virtualenv (recommended)

### Setup
```bash
# From project root
python -m venv venv
# Windows
venv\Scripts\activate
pip install -r requirements.txt

# Run dev server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000/` in your browser.

### Frontend
- Dashboard: `static/dashboard.html`
- Main script: `static/dashboard.js`

## API Overview
- Auth: `/api/register`, `/api/login`, `/api/verify-token`
- Projects: `/api/projects` (GET/POST), `/api/projects/{id}` (GET/PUT)
- Agents: `/api/agent/material-search`, `/api/agent/estimate`, `/api/agent/advice`, `/api/agent/report`, `/api/agent/coordinate`
- Reports: `/api/projects/{id}/report` (PDF/JSON)

## Data Files
- Materials: `materials_ontario*.json`
- Prices: `prices_ontario*.json`

## Notes
- Ensure you have a valid auth token for protected endpoints.
- Update database configuration if needed (`database_config.py`).
- If form navigation blocks on Next Step, required fields must be filled; see `dashboard.js` validation.

## License
MIT (or choose one you prefer).