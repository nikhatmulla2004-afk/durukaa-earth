# Darukaa Earth — Local Setup

## Backend (FastAPI)

1. Create and activate virtualenv:

```powershell
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:

```powershell
pip install -r backend/requirements.txt
```

3. Run the backend:

```powershell
cd backend
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs to view API docs.

## Frontend (Vite + React)

1. From project root:

```bash
cd frontend
npm install
npm run dev
```

2. Open the Vite local URL shown in the terminal.

3. If deploying, update `API_BASE` in `frontend/src/App.jsx` to point to your live backend.
