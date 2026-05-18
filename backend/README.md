# LegalVault Backend

Flask backend foundation for LegalVault, with CORS, MongoDB Atlas, JWT helpers, and a health check route.

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Health check:

```text
GET http://127.0.0.1:5000/api/status
```

Auth routes:

```text
POST http://127.0.0.1:5000/auth/register
POST http://127.0.0.1:5000/auth/login
GET  http://127.0.0.1:5000/auth/me
```

Document routes require `Authorization: Bearer <token>`:

```text
POST http://127.0.0.1:5000/upload
GET  http://127.0.0.1:5000/documents
GET  http://127.0.0.1:5000/documents/<document_id>/text
POST http://127.0.0.1:5000/documents/<document_id>/process
```
