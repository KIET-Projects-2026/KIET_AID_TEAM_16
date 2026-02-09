# Backend (Flask)

Quick start:

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
# ensure MongoDB is running locally, or set MONGO_URI in .env
python app.py
```

Endpoints:
- POST /api/auth/signup  {name,email,password,role}
- POST /api/auth/login   {email,password}
- GET  /api/auth/me      (Bearer token)
- GET  /api/auth/users?role=patient
- POST /api/chat/ask     {question} (Bearer token)
- GET  /api/chat/history (Bearer token)
- Doctor endpoints: /api/chat/patient/<id>/history, /api/chat/patient/<id>/suggest

Notes:
- Model is loaded lazily; if no finetuned model is present it will fall back to `BASE_MODEL` from config.
- For this demo, the backend enforces that user emails must be `@gmail.com` (both signup and login); update or remove this requirement in `backend/routes/auth.py` if you want other domains.
