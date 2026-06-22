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
GET  http://127.0.0.1:5000/protected
```

Registration accepts `name`, `email`, `password`, and optional `role` (`user` or `admin`). Public registrations should use `user`; registering an `admin` also requires `admin_key` matching `ADMIN_REGISTRATION_KEY`. Passwords are hashed with bcrypt, users are stored in MongoDB, and access tokens are JWTs with role claims and a configurable expiry via `JWT_ACCESS_TOKEN_EXPIRES_MINUTES`.

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
