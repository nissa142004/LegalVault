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
GET  http://127.0.0.1:5000/protected
```

Document routes require `Authorization: Bearer <token>`:

```text
POST http://127.0.0.1:5000/upload
GET  http://127.0.0.1:5000/documents
GET  http://127.0.0.1:5000/documents/<document_id>/text
POST http://127.0.0.1:5000/process-document/<document_id>
POST http://127.0.0.1:5000/extract-keywords/<document_id>
POST http://127.0.0.1:5000/summarize/<document_id>
POST http://127.0.0.1:5000/documents/<document_id>/process
```

Upload requests should use `multipart/form-data` with a `file` field. PDF and DOCX files are stored in `backend/uploads`, and document metadata is saved in MongoDB with `filename`, `filepath`, `upload_date`, and `uploaded_by`.

Text extraction uses PyPDF2 for PDFs and python-docx for DOCX files. Processed document records store `raw_text` and `cleaned_text`; preprocessing lowercases text, removes punctuation, tokenizes with NLTK, and removes stopwords.

Keyword extraction uses RAKE-NLTK on cleaned document text and stores the extracted phrases in the document's `keywords` field.

Summarization uses Sumy's TextRank summarizer and stores the generated extractive summary in the document's `summary` field. Pass an optional JSON body like `{"sentence_count": 5}` to control summary length.
