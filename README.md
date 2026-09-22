# LegalVault

<p align="center">
  <img src="frontend/public/legalvault-logo.png" alt="LegalVault logo" width="120" />
</p>

<p align="center">
  A secure workspace for storing, organizing, searching, and understanding legal documents.
</p>

<p align="center">
  <a href="#features">Features</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="#api-documentation">API</a> ·
  <a href="#machine-learning">Machine learning</a> ·
  <a href="#security-notes">Security</a>
</p>

LegalVault helps legal teams keep documents in one place while making them easier to work with. Upload a PDF or DOCX file, capture matter and governance metadata, automatically extract its text and keywords, classify it, find related material, and review activity from a single dashboard.

> **Disclaimer:** LegalVault is a document-management and productivity tool. Its generated categories, keywords, summaries, and similarity results are assistive only and must be reviewed by a qualified professional.

## Features

- Secure account registration, sign-in, professional profiles, and password-reset emails.
- User-scoped document storage with JWT-protected APIs.
- PDF and DOCX uploads with safe filenames and automatic text extraction.
- Document metadata for matters, clients, confidentiality, privilege, retention, and review status.
- Keyword extraction and extractive TextRank summaries.
- TF–IDF and Multinomial Naive Bayes document categorization with confidence scores and low-confidence review flags.
- Relevance-ranked document search and related-document recommendations.
- Dashboard analytics for document volume, categories, processing, governance, and recent uploads.
- Interactive OpenAPI/Swagger documentation generated from the Flask routes.
- Responsive React interface with light and dark themes.

## Tech stack

| Area | Technologies |
| --- | --- |
| Frontend | React 18, Vite, React Router, Axios, Tailwind CSS, Framer Motion |
| Backend | Python, Flask, Flask-JWT-Extended, Flask-CORS |
| Data | MongoDB / PyMongo |
| Document processing | PyPDF2, python-docx, NLTK, RAKE, Sumy |
| ML and search | scikit-learn, pandas, joblib, TF–IDF |
| API documentation | Flasgger / OpenAPI 3.0 |

## Project structure

```text
LegalVault/
├── frontend/                 # React + Vite application
│   └── src/
│       ├── pages/            # Auth, dashboard, documents, search, profile
│       ├── components/       # Shared UI elements
│       └── api/              # Axios API client
└── backend/                  # Flask REST API
    ├── routes/               # Auth, documents, AI, analytics, status endpoints
    ├── services/             # Extraction, preprocessing, similarity, email
    ├── models/               # MongoDB persistence models
    ├── ml/                   # Classifier and saved artifacts
    ├── docs/                 # OpenAPI configuration
    ├── tests/                # Regression tests
    └── uploads/              # Runtime document storage (not committed)
```

## Prerequisites

- Python 3.12+
- Node.js 18+
- MongoDB running locally or a MongoDB-compatible connection string

## Quick start

### 1. Configure and start the backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
python app.py
```

The API starts at `http://127.0.0.1:5000` by default. Confirm that the API and MongoDB are reachable:

```bash
curl http://127.0.0.1:5000/api/status
```

Expected response:

```json
{
  "service": "LegalVault Backend",
  "status": "ok",
  "mongodb": "connected"
}
```

### 2. Configure and start the frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

The frontend calls `http://<current-host>:5000` if no API URL is configured. To use a different backend address, create `frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:5001
```

Then start the backend on the matching port:

```bash
cd backend
FLASK_PORT=5001 python app.py
```

## Configuration

Copy `backend/.env.example` to `backend/.env`; never commit the resulting file. The key settings are:

| Variable | Purpose |
| --- | --- |
| `MONGO_URI` | MongoDB connection string |
| `MONGO_DB_NAME` | Database name; defaults to `LegalVault` |
| `JWT_SECRET` | Long, randomly generated signing secret |
| `CORS_ORIGINS` | Allowed frontend origin(s) |
| `FLASK_HOST` / `FLASK_PORT` | API bind address and port |
| `UPLOAD_FOLDER` | Directory for original uploaded files |
| `MAX_UPLOAD_MB` | Maximum upload size; defaults to 10 MB |
| `MAIL_*` | SMTP settings used by password reset |
| `FRONTEND_URL` | Base URL used in password-reset links |
| `CLASSIFIER_MODEL_PATH` | Optional path to the trained category model |

For local use, start MongoDB before launching the API. A typical local URI is `mongodb://localhost:27017`.

## API documentation

With the backend running, browse the interactive API reference at:

- [Swagger UI](http://127.0.0.1:5000/api/v1/docs/)
- [OpenAPI JSON](http://127.0.0.1:5000/api/v1/openapi.json)

Most document, analytics, and profile endpoints require a bearer token returned by `/auth/register` or `/auth/login`.

| Area | Example endpoints |
| --- | --- |
| Health | `GET /api/status` |
| Authentication | `POST /auth/register`, `POST /auth/login`, `POST /auth/forgot-password` |
| Documents | `POST /documents/upload`, `GET /documents`, `PATCH /documents/:id` |
| AI tools | `POST /predict-category`, `POST /search`, `POST /documents/:id/summarize` |
| Analytics | `GET /analytics/dashboard` |

## Machine learning

LegalVault uses a scikit-learn pipeline with TF–IDF features (unigrams and bigrams) and a Multinomial Naive Bayes classifier. It supports these categories:

`Case Law` · `Contract` · `Employment` · `Lease` · `Property`

Train or replace the model with a CSV containing `text` and `label` columns:

```bash
cd backend
source .venv/bin/activate
python scripts/train_classifier.py --dataset /absolute/path/to/legal_documents.csv
```

The script makes a stratified 80/20 train/test split and writes the artifacts to:

```text
backend/ml/artifacts/legal_category_model.joblib
backend/ml/artifacts/evaluation.json
```

Inspect the saved evaluation report with:

```bash
cd backend
python -m json.tool ml/artifacts/evaluation.json
```

Classification confidence below 50% is surfaced as a manual-review recommendation rather than an automatic assignment.

## Testing and production build

Run backend regression tests:

```bash
cd backend
source .venv/bin/activate
python -m unittest discover -s tests
```

Build the frontend for production:

```bash
cd frontend
npm run build
```

## Security notes

- Use a unique, high-entropy `JWT_SECRET` outside local development.
- Set `CORS_ORIGINS` to the exact deployed frontend origin rather than `*`.
- Use managed, encrypted storage and a production MongoDB deployment for sensitive documents.
- Configure SMTP credentials through environment variables or a secret manager.
- Uploaded documents are intentionally excluded from Git; only `backend/uploads/.gitkeep` is tracked.
- The application enforces ownership checks for document operations, but deployment controls such as TLS, backups, retention policies, audit logging, and access reviews remain essential.

## Contributing

1. Fork the repository and create a focused branch.
2. Keep changes scoped and add or update tests for backend behavior.
3. Run the test suite and frontend build before opening a pull request.
4. Never include documents, `.env` files, credentials, or other sensitive data in commits.

## License

No license has been specified yet. Add a license file before distributing or accepting external contributions.
