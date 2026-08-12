# LegalVault Backend

Flask backend foundation for LegalVault, with CORS, MongoDB Atlas, JWT authentication, and a health check route.

## Setup

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Interactive API documentation

The backend uses Flasgger and OpenAPI 3.0.3. After starting Flask, open:

```text
Swagger UI:   http://localhost:5000/api/v1/docs
OpenAPI JSON: http://localhost:5000/api/v1/openapi.json
```

Authorize protected operations by selecting **Authorize** and entering the JWT
returned by `/auth/login`. Swagger UI adds the `Bearer` prefix through the
OpenAPI HTTP bearer security scheme.

The relevant project structure is:

```text
backend/
├── app.py                 # application factory and extension registration
├── docs/
│   └── openapi.py         # OpenAPI components, metadata, and route discovery
├── routes/                # HTTP routing/controllers grouped by feature
├── models/                # MongoDB access and serialization
├── services/              # reusable application and AI business logic
├── utils/
│   └── config.py          # environment and Flasgger configuration
├── requirements.txt
└── .env.example
```

Install only the documentation dependency in an existing environment with:

```powershell
python -m pip install flasgger==0.9.7.1
```

`init_api_docs(app)` runs after all blueprints are registered. It walks Flask's
URL map and attaches a complete fallback operation to every route, so a new
endpoint is automatically included in the generated JSON. For polished wording,
add the endpoint's Flask endpoint name to `OPERATIONS` in `docs/openapi.py`. Add
a reusable body schema to `SCHEMAS` and `JSON_BODIES` when the endpoint accepts
JSON. Shared error responses, path parameters, JWT security, request/response
examples, and standard status codes are generated centrally.

Health check:

```text
GET http://127.0.0.1:5000/api/status
```

Auth routes:

```text
POST http://127.0.0.1:5000/auth/register
POST http://127.0.0.1:5000/auth/login
GET  http://127.0.0.1:5000/auth/me
GET  http://127.0.0.1:5000/auth/profile
POST http://127.0.0.1:5000/auth/forgot-password
POST http://127.0.0.1:5000/auth/reset-password
PATCH http://127.0.0.1:5000/auth/profile
GET  http://127.0.0.1:5000/protected
```

Registration accepts `name`, `email`, `password`, optional professional profile fields (`phone`, `organization`, `job_title`, `jurisdiction`, `professional_id`), and optional `role` (`user` or `admin`). A branded welcome email is sent through the SMTP settings in `.env`. Password reset links are signed, single-use, and expire after `PASSWORD_RESET_MAX_AGE_SECONDS` (one hour by default). Public registrations should use `user`; registering an `admin` also requires `admin_key` matching `ADMIN_REGISTRATION_KEY`. Passwords are hashed with bcrypt, users are stored in MongoDB, and access tokens are JWTs with role claims and a configurable expiry via `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`.

Document routes require `Authorization: Bearer <token>`:

```text
POST http://127.0.0.1:5000/documents/upload
GET  http://127.0.0.1:5000/documents
GET  http://127.0.0.1:5000/documents/<document_id>
GET  http://127.0.0.1:5000/documents/<document_id>/text
DELETE http://127.0.0.1:5000/documents/<document_id>
POST http://127.0.0.1:5000/process-document/<document_id>
POST http://127.0.0.1:5000/extract-keywords/<document_id>
POST http://127.0.0.1:5000/summarize/<document_id>
POST http://127.0.0.1:5000/documents/<document_id>/process
POST http://127.0.0.1:5000/search
```

Upload requests should use `multipart/form-data` with a `file` field. PDF and DOCX files are stored in `backend/uploads`, and document metadata is saved in MongoDB with `filename`, `filepath`, `upload_date`, and `uploaded_by`. Upload size is limited by `MAX_UPLOAD_MB`, which defaults to 10 MB.

Text extraction uses `services/text_extractor.py`: PyPDF2 for PDFs and python-docx for DOCX files. Processed document records store `raw_text` and `cleaned_text` in MongoDB. Preprocessing uses `services/text_preprocessor.py` to lowercase text, remove punctuation, tokenize with NLTK, remove stopwords, and lemmatize terms when NLTK WordNet or spaCy is available.

Keyword extraction uses legal-domain RAKE scoring on the original document text, removes boilerplate and near-duplicates, and stores up to 10 short ranked phrases in the document's `keywords` field. `POST /extract-keywords/<document_id>` returns `{"keywords": [...]}`.

Summarization uses Sumy's TextRank summarizer and stores the generated extractive summary in the document's `summary` field. Pass an optional JSON body like `{"sentence_count": 5}` to control summary length.

Legal search uses scikit-learn's TF-IDF vectorizer and cosine similarity to rank the authenticated user's cleaned legal documents. Send:

```json
{
  "query": "tenant eviction notice requirements"
}
```

The response returns the top 5 matches with `title`, `similarity_score`, `summary`, and `keywords`.

## Legal document classification

Train the TF-IDF + Multinomial Naive Bayes classifier from the project root:

```powershell
python backend\scripts\train_classifier.py --dataset "C:\path\to\legal_dataset.csv"
```

The script performs a stratified 80/20 train/test split, prints accuracy, writes the
joblib model to `backend/ml/artifacts/legal_category_model.joblib`, and writes full
evaluation metrics to `backend/ml/artifacts/evaluation.json`.

Classify document text (this route does not require authentication):

```text
POST http://127.0.0.1:5000/predict-category
Content-Type: application/json
```

```json
{
  "text": "This employment agreement describes salary, leave, and termination."
}
```

The response includes the predicted `category`, its `confidence`, probabilities for
all five categories, and the model version. Set `CLASSIFIER_MODEL_PATH` to use an
artifact stored elsewhere.

## Analytics dashboard

The authenticated frontend dashboard loads live, user-scoped analytics from:

```text
GET http://127.0.0.1:5000/analytics/dashboard
Authorization: Bearer <token>
```

The response includes total documents, ML category distribution, five most recent
uploads, AI processing completion statistics, and upload counts for the last seven
days. New uploads are categorized automatically by the saved classifier. The React
dashboard refreshes this data every 30 seconds and also provides a manual refresh.

## Advanced AI intelligence upgrade

Updated architecture:

```text
backend/
  ml/classifier.py              cached trained TF-IDF + MultinomialNB inference
  services/similarity.py        reusable TF-IDF index cache + cosine ranking
  services/evaluation.py        classification metrics + ROUGE/compression metrics
  routes/documents.py           upload, smart search, recommendation APIs
  routes/analytics.py           dashboard and model evaluation APIs
  models/document.py            MongoDB document schema/serialization helpers
  utils/nlp_processing.py       RAKE-style keywords and TextRank summarization
```

MongoDB document records now store AI metadata automatically during upload:

```json
{
  "filename": "employment.pdf",
  "filepath": "backend/uploads/<uuid>.pdf",
  "uploaded_by": "<user_id>",
  "raw_text": "...",
  "cleaned_text": "...",
  "predicted_category": "Employment",
  "confidence_score": 0.92,
  "classification_status": "assigned",
  "classification_warning": null,
  "top_predictions": [
    {"category": "Employment", "probability": 0.92, "percentage": 92.0}
  ],
  "keywords": ["termination clause", "salary payment"],
  "summary": "...",
  "upload_date": "2026-06-23T...",
  "updated_at": "2026-06-23T..."
}
```

Low-confidence behavior: if classifier confidence is below `50%`, upload stores
`predicted_category` as `Uncategorized`, sets `classification_status` to
`manual_review`, keeps the confidence/top-three predictions for review, and
returns a warning such as `Low confidence prediction (45%). Manual review recommended.`

New and enhanced APIs:

```text
POST /predict-category
```

Returns `predicted_category`, `confidence_score`, `confidence_percentage`,
`top_predictions`, all class `probabilities`, `is_low_confidence`, and `warning`.

```text
POST /documents/upload
```

Runs extraction, preprocessing, classification, keyword extraction, TextRank
summary, metadata storage, and top-5 similar document recommendation in one
authenticated upload flow.

```text
GET /documents/<document_id>/recommendations?same_category=true
GET /documents/<document_id>/recommendations?same_category=false
GET /documents/<document_id>/recommendations?category=Contract
```

Returns top similar documents ranked by TF-IDF cosine similarity with
`document_name` and `similarity_percentage`.

```text
POST /search
```

Smart search now classifies the query first. If confidence is strong, TF-IDF
cosine ranking is restricted to the predicted category; otherwise it searches all
user documents.

```text
GET /analytics/evaluation
GET /analytics/evaluation/classification
GET /analytics/evaluation/summarization
```

Classification metrics return accuracy, precision, recall, F1-score,
classification report, labels, and confusion matrix from
`ml/artifacts/evaluation.json`. Summarization metrics return ROUGE-1, ROUGE-L
when documents include `reference_summary` or `gold_summary`, plus compression
ratio for generated summaries.

Integration steps:

1. Train or retrain the classifier with `python backend\scripts\train_classifier.py --dataset "C:\path\to\legal_dataset.csv"`.
2. Start Flask after confirming `.env` has `MONGO_URI`; optionally set `CLASSIFIER_MODEL_PATH` and `CLASSIFIER_METRICS_PATH`.
3. Upload PDFs/DOCX through `POST /documents/upload`; no separate keyword or summary call is required for new documents.
4. Use `classification_status == "manual_review"` in admin/reviewer UI to queue uncertain documents.
5. Use `/documents/<id>/recommendations` on the document detail screen for related-document cards.
6. Replace plain search result calls with the enhanced `/search` response and show `category_filter` when available.
7. Build the evaluation dashboard from `/analytics/evaluation`: charts for confusion matrix and class metrics, plus summary compression/ROUGE cards.

React integration mapping:

```text
Upload success modal/card:
  response.document.predicted_category
  response.classification.confidence_percentage
  response.classification.top_predictions
  response.classification.warning
  response.similar_documents

Document list/detail:
  document.predicted_category
  document.confidence_score
  document.classification_status
  document.keywords
  document.summary

Smart search page:
  response.query_classification.predicted_category
  response.category_filter
  response.results[].similarity_percentage

Recommendation panel:
  GET /documents/<id>/recommendations
  recommendations[].document_name
  recommendations[].similarity_percentage

Evaluation dashboard:
  classification.accuracy / precision / recall / f1_score
  classification.confusion_matrix + labels
  summarization.rouge_1 / rouge_l / compression_ratio
```
http://localhost:5000/api/v1/docs