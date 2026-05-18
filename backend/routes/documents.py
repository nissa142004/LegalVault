from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.utils import secure_filename

from models.document import (
    create_document,
    find_document_by_id,
    find_documents_by_user,
    serialize_document,
    serialize_document_nlp,
    serialize_document_text,
    update_document_keywords,
    update_document_summary,
    update_document_text,
    update_document_nlp,
)
from utils.auth_middleware import auth_required
from utils.nlp_processing import extract_keywords, summarize_textrank
from utils.text_extraction import extract_text, preprocess_text

documents_bp = Blueprint("documents", __name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@documents_bp.post("/upload")
@auth_required
def upload_document():
    if "file" not in request.files:
        return jsonify({"message": "A file field is required."}), 400

    file = request.files["file"]
    if not file or not file.filename:
        return jsonify({"message": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"message": "Only PDF and DOCX files are allowed."}), 400

    original_name = secure_filename(file.filename)
    if not original_name:
        return jsonify({"message": "Invalid filename."}), 400

    extension = Path(original_name).suffix.lower()
    stored_filename = f"{uuid4().hex}{extension}"
    upload_path = Path(current_app.config["UPLOAD_FOLDER"])
    upload_path.mkdir(parents=True, exist_ok=True)

    file_path = upload_path / stored_filename
    file.save(file_path)

    try:
        raw_text = extract_text(file_path)
        cleaned_text = preprocess_text(raw_text)
    except Exception:
        file_path.unlink(missing_ok=True)
        return jsonify({"message": "Unable to extract text from this document."}), 422

    document = create_document(
        filename=original_name,
        filepath=str(file_path),
        uploaded_by=str(g.current_user["_id"]),
        raw_text=raw_text,
        cleaned_text=cleaned_text,
    )

    return jsonify({"document": serialize_document_text(document)}), 201


@documents_bp.get("/documents")
@auth_required
def list_documents():
    documents = find_documents_by_user(str(g.current_user["_id"]))

    return jsonify(
        {"documents": [serialize_document(document) for document in documents]}
    ), 200


@documents_bp.get("/documents/<document_id>/text")
@auth_required
def get_document_text(document_id):
    document = find_document_by_id(document_id, str(g.current_user["_id"]))
    if not document:
        return jsonify({"message": "Document not found."}), 404

    return jsonify({"document": serialize_document_text(document)}), 200


@documents_bp.post("/process-document/<document_id>")
@auth_required
def process_document_text(document_id):
    document = find_document_by_id(document_id, str(g.current_user["_id"]))
    if not document:
        return jsonify({"message": "Document not found."}), 404

    filepath = document.get("filepath")
    if not filepath:
        return jsonify({"message": "Document file path is missing."}), 422

    file_path = Path(filepath)
    if not file_path.exists():
        return jsonify({"message": "Document file is missing from storage."}), 404

    try:
        raw_text = extract_text(file_path)
        cleaned_text = preprocess_text(raw_text)
    except Exception:
        return jsonify({"message": "Unable to process this document."}), 422

    updated_document = update_document_text(
        document_id=document_id,
        user_id=str(g.current_user["_id"]),
        raw_text=raw_text,
        cleaned_text=cleaned_text,
    )

    return jsonify({"document": serialize_document_text(updated_document)}), 200


@documents_bp.post("/extract-keywords/<document_id>")
@auth_required
def extract_document_keywords(document_id):
    document = find_document_by_id(document_id, str(g.current_user["_id"]))
    if not document:
        return jsonify({"message": "Document not found."}), 404

    text = document.get("cleaned_text") or document.get("raw_text", "")
    if not text:
        return jsonify({"message": "Document has no text to extract keywords from."}), 422

    keywords = extract_keywords(text)
    updated_document = update_document_keywords(
        document_id=document_id,
        user_id=str(g.current_user["_id"]),
        keywords=keywords,
    )

    return jsonify({"document": serialize_document_nlp(updated_document)}), 200


@documents_bp.post("/summarize/<document_id>")
@auth_required
def summarize_document(document_id):
    document = find_document_by_id(document_id, str(g.current_user["_id"]))
    if not document:
        return jsonify({"message": "Document not found."}), 404

    data = request.get_json(silent=True) or {}
    sentence_count = data.get("sentence_count", data.get("sentences", 3))
    try:
        sentence_count = int(sentence_count)
    except (TypeError, ValueError):
        return jsonify({"message": "sentence_count must be a number."}), 400

    if sentence_count < 1 or sentence_count > 20:
        return jsonify({"message": "sentence_count must be between 1 and 20."}), 400

    text = document.get("raw_text", document.get("extracted_text", ""))
    if not text:
        return jsonify({"message": "Document has no text to summarize."}), 422

    summary = summarize_textrank(text, max_sentences=sentence_count)
    updated_document = update_document_summary(
        document_id=document_id,
        user_id=str(g.current_user["_id"]),
        summary=summary,
        summary_sentence_count=sentence_count,
    )

    return jsonify({"document": serialize_document_nlp(updated_document)}), 200


@documents_bp.post("/documents/<document_id>/process")
@auth_required
def process_document(document_id):
    document = find_document_by_id(document_id, str(g.current_user["_id"]))
    if not document:
        return jsonify({"message": "Document not found."}), 404

    text = document.get("cleaned_text") or document.get(
        "raw_text",
        document.get("extracted_text", ""),
    )
    if not text:
        return jsonify({"message": "Document has no extracted text to process."}), 422

    keywords = extract_keywords(text)
    summary = summarize_textrank(document.get("raw_text", text))
    updated_document = update_document_nlp(
        document_id=document_id,
        user_id=str(g.current_user["_id"]),
        keywords=keywords,
        summary=summary,
    )

    return jsonify({"document": serialize_document_nlp(updated_document)}), 200
