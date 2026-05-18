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
    update_document_nlp,
)
from utils.auth_middleware import auth_required
from utils.nlp_processing import extract_keywords, summarize_textrank
from utils.text_extraction import clean_text, extract_text

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
    extension = Path(original_name).suffix.lower()
    stored_filename = f"{uuid4().hex}{extension}"
    upload_path = Path(current_app.config["UPLOAD_FOLDER"])
    upload_path.mkdir(parents=True, exist_ok=True)

    file_path = upload_path / stored_filename
    file.save(file_path)

    try:
        extracted_text = extract_text(file_path)
        cleaned_text = clean_text(extracted_text)
    except Exception:
        file_path.unlink(missing_ok=True)
        return jsonify({"message": "Unable to extract text from this document."}), 422

    document = create_document(
        filename=stored_filename,
        user_id=str(g.current_user["_id"]),
        extracted_text=extracted_text,
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


@documents_bp.post("/documents/<document_id>/process")
@auth_required
def process_document(document_id):
    document = find_document_by_id(document_id, str(g.current_user["_id"]))
    if not document:
        return jsonify({"message": "Document not found."}), 404

    extracted_text = document.get("extracted_text", "")
    if not extracted_text:
        return jsonify({"message": "Document has no extracted text to process."}), 422

    keywords = extract_keywords(extracted_text)
    summary = summarize_textrank(extracted_text)
    updated_document = update_document_nlp(
        document_id=document_id,
        user_id=str(g.current_user["_id"]),
        keywords=keywords,
        summary=summary,
    )

    return jsonify({"document": serialize_document_nlp(updated_document)}), 200
