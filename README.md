# SafeRoute

![GitHub repo status](https://img.shields.io/badge/status-active%20project-success)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)
![React](https://img.shields.io/badge/React-19-61DAFB)
![Flask](https://img.shields.io/badge/Flask-3.1-000000)

SafeRoute is a full-stack personal safety web app that helps users track journeys, monitor suspicious activity, verify safety, and alert trusted contacts when needed.

The app combines a Flask REST API with a React frontend and is designed for a personal safety workflow using GPS, route monitoring, anomaly detection, and emergency escalation.

> This project is a safety aid, not a replacement for emergency services or official navigation apps.

---

## Features

- User registration and login
- JWT-based authentication
- Emergency contact management
- Journey start, pause, resume, and end flow
- GPS location tracking and monitoring
- Route anomaly and safety checks
- Live safety verification prompts
- SOS-trigger workflow and trusted-contact alerts
- Frontend dashboard and map views

---

## Tech stack

| Layer | Technology |
|------|------------|
| Frontend | React + Vite |
| Backend | Python Flask |
| Database | SQLite for local development |
| Auth | Flask-JWT-Extended |
| Maps | Leaflet + OpenStreetMap |
| Data | JSON/DB-backed safety and hotspot logic |

---

## Project structure

```text
majorprojet-main/
├── backend/
│   ├── app/
│   ├── data/
│   ├── tests/
│   ├── .env.example
│   ├── requirements.txt
│   └── run.py
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.js
├── docs/
├── .gitignore
├── README.md
├── package.json
└── package-lock.json
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- npm
- Git

---

## Backend setup

From the project root:

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env
python run.py
```

The API runs at:

- http://localhost:5000
- Health endpoint: http://localhost:5000/api/health

---

## Frontend setup

From the project root:

```bash
cd frontend
copy .env.example .env
npm install
npm run dev -- --host 0.0.0.0
```

Open the app at:

- http://localhost:5173

---

## Environment variables

### Backend

Create `backend/.env` based on `backend/.env.example`.

Key values:

- `SECRET_KEY`
- `JWT_SECRET_KEY`
- `DATABASE_URL`
- `CORS_ORIGINS`
- `FRONTEND_URL`

### Frontend

Create `frontend/.env` based on `frontend/.env.example`.

Example:

```env
VITE_API_BASE_URL=http://127.0.0.1:5000/api
```

---

## Main API flow

### Auth

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `PUT /api/auth/me`

### Contacts

- `GET /api/contacts`
- `POST /api/contacts`
- `PUT /api/contacts/:id`
- `DELETE /api/contacts/:id`

### Journeys

- `GET /api/journeys/active`
- `POST /api/journeys`
- `POST /api/journeys/:id/pause`
- `POST /api/journeys/:id/resume`
- `POST /api/journeys/:id/end`
- `POST /api/journeys/:id/sos`
- `POST /api/journeys/:id/locations`
- `GET /api/journeys/:id/monitoring`

### Safety checks

- `POST /api/safety-checks/:id/respond`
- `POST /api/safety-checks/:id/cancel-countdown`
- `POST /api/safety-checks/:id/timeout`

---

## Git workflow

```bash
git checkout -b feature/my-change
git add .
git commit -m "Add my feature"
git push origin feature/my-change
```

For main branch updates:

```bash
git checkout main
git pull origin main
git merge feature/my-change
git push origin main
```

---

## Notes

- Do not commit environment files or Firebase credentials.
- Keep production secrets out of the repository.
- The SQLite database is created automatically at runtime in the backend instance folder for local development.

---

## License

This project is currently provided as an open-source project for learning and demo use.
