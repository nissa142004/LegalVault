from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, g, jsonify, request, send_file
from werkzeug.utils import secure_filename

from models.document import (
    create_document,
    delete_document_by_id,
    find_document_by_id,
    find_documents_by_user,
    serialize_document,
    serialize_document_nlp,
    serialize_document_text,
    top_keywords,
    update_document_keywords,
    update_document_summary,
    update_document_text,
)
from utils.auth_middleware import auth_required
from utils.nlp_processing import (
    extract_keywords,
    summarize_textrank,
)
from services.similarity import rank_documents_by_similarity
from services.text_extractor import SUPPORTED_EXTENSIONS, extract_text
from services.text_preprocessor import preprocess_text
from ml.classifier import ModelNotAvailableError, predict_category

documents_bp = Blueprint("documents", __name__)

ALLOWED_EXTENSIONS = SUPPORTED_EXTENSIONS
MAX_KEYWORDS = 10


def allowed_file(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@auth_required
def handle_upload_document():
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

    predicted_category = "Uncategorized"
    confidence_score = None
    classification_status = "unavailable"
    classification_warning = None
    top_predictions = []
    if raw_text.strip():
        try:
            classification = predict_category(
                raw_text, current_app.config["CLASSIFIER_MODEL_PATH"]
            )
            confidence_score = classification["confidence_score"]
            classification_warning = classification.get("warning")
            top_predictions = classification.get("top_predictions", [])
            if classification["is_low_confidence"]:
                classification_status = "manual_review"
            else:
                predicted_category = classification["predicted_category"]
                classification_status = "assigned"
        except ModelNotAvailableError:
            current_app.logger.warning("Uploaded document could not be categorized: model unavailable")

    keywords = extract_keywords(raw_text, max_keywords=MAX_KEYWORDS)
    summary = ""

    document = create_document(
        filename=original_name,
        filepath=str(file_path),
        uploaded_by=str(g.current_user["_id"]),
        raw_text=raw_text,
        cleaned_text=cleaned_text,
        predicted_category=predicted_category,
        confidence_score=confidence_score,
        keywords=keywords,
        summary=summary,
        classification_status=classification_status,
        classification_warning=classification_warning,
        top_predictions=top_predictions,
    )

    all_documents = find_documents_by_user(str(g.current_user["_id"]))
    recommendations = _recommendations_for_text(
        raw_text,
        all_documents,
        predicted_category if classification_status == "assigned" else None,
        exclude_document_id=str(document["_id"]),
    )

    return jsonify(
        {
            "document": serialize_document_text(document),
            "classification": {
                "predicted_category": predicted_category,
                "confidence_score": confidence_score,
                "confidence_percentage": (
                    round(confidence_score * 100, 2)
                    if confidence_score is not None
                    else None
                ),
                "status": classification_status,
                "warning": classification_warning,
                "top_predictions": top_predictions,
            },
            "similar_documents": recommendations,
        }
    ), 201


@documents_bp.post("/documents/upload")
def upload_document():
    return handle_upload_document()


@documents_bp.post("/upload")
def upload_document_legacy():
    return handle_upload_document()


@documents_bp.get("/documents")
@auth_required
def list_documents():
    documents = find_documents_by_user(str(g.current_user["_id"]))

    return jsonify(
        {"documents": [serialize_document(document) for document in documents]}
    ), 200


@documents_bp.get("/documents/<document_id>")
@auth_required
def get_document(document_id):
    document = find_document_by_id(document_id, str(g.current_user["_id"]))
    if not document:
        return jsonify({"message": "Document not found."}), 404

    return jsonify({"document": serialize_document(document)}), 200


@documents_bp.post("/search")
@auth_required
def search_documents():
    data = request.get_json(silent=True) or {}
    query = str(data.get("query", "")).strip()
    if not query:
        return jsonify({"message": "A search query is required."}), 400

    documents = find_documents_by_user(str(g.current_user["_id"]))
    query_classification = None
    category_filter = None
    try:
        query_classification = predict_category(
            query, current_app.config["CLASSIFIER_MODEL_PATH"]
        )
        if not query_classification["is_low_confidence"]:
            category_filter = query_classification["predicted_category"]
    except ModelNotAvailableError:
        current_app.logger.warning("Search query classification skipped: model unavailable")

    ranked_matches = rank_documents_by_similarity(
        query,
        documents,
        max_results=5,
        category=category_filter,
        cache_namespace=f"search:{g.current_user['_id']}",
    )

    results = []
    for match in ranked_matches:
        document = match["document"]
        text = document.get("cleaned_text") or document.get("raw_text", "")
        raw_text = document.get("raw_text", text)
        keywords = top_keywords(document) or extract_keywords(raw_text, max_keywords=MAX_KEYWORDS)
        summary = document.get("summary", "") if document.get("summary_generated_at") else ""

        results.append(
            {
                "document_id": str(document["_id"]),
                "title": document["filename"],
                "similarity_score": match["score"],
                "similarity_percentage": match["similarity_percentage"],
                "predicted_category": document.get("predicted_category", document.get("category", "Uncategorized")),
                "summary": summary,
                "keywords": keywords,
            }
        )

    return jsonify(
        {
            "query": query,
            "query_classification": query_classification,
            "category_filter": category_filter,
            "results": results,
        }
    ), 200


def _recommendations_for_text(
    text: str,
    documents: list[dict],
    category: str | None,
    exclude_document_id: str | None = None,
) -> list[dict]:
    ranked_matches = rank_documents_by_similarity(
        text,
        documents,
        max_results=5,
        category=category,
        cache_namespace=f"recommendations:{category or 'all'}",
        exclude_document_id=exclude_document_id,
    )
    return [
        {
            "document_id": str(match["document"]["_id"]),
            "document_name": match["document"]["filename"],
            "similarity_score": match["score"],
            "similarity_percentage": match["similarity_percentage"],
            "predicted_category": match["document"].get(
                "predicted_category",
                match["document"].get("category", "Uncategorized"),
            ),
        }
        for match in ranked_matches
    ]


@documents_bp.get("/documents/<document_id>/recommendations")
@auth_required
def recommend_similar_documents(document_id):
    document = find_document_by_id(document_id, str(g.current_user["_id"]))
    if not document:
        return jsonify({"message": "Document not found."}), 404

    category = request.args.get("category")
    if category is None and request.args.get("same_category", "true").lower() != "false":
        category = document.get("predicted_category") or document.get("category")
        if category == "Uncategorized":
            category = None

    text = document.get("cleaned_text") or document.get("raw_text", "")
    documents = find_documents_by_user(str(g.current_user["_id"]))
    recommendations = _recommendations_for_text(
        text,
        documents,
        category,
        exclude_document_id=document_id,
    )
    return jsonify(
        {
            "document_id": document_id,
            "category_filter": category,
            "recommendations": recommendations,
        }
    ), 200


@documents_bp.get("/documents/<document_id>/text")
@auth_required
def get_document_text(document_id):
    document = find_document_by_id(document_id, str(g.current_user["_id"]))
    if not document:
        return jsonify({"message": "Document not found."}), 404

    return jsonify({"document": serialize_document_text(document)}), 200


@documents_bp.get("/documents/<document_id>/original")
@auth_required
def view_original_document(document_id):
    document = find_document_by_id(document_id, str(g.current_user["_id"]))
    if not document:
        return jsonify({"message": "Document not found."}), 404

    filepath = document.get("filepath")
    if not filepath:
        return jsonify({"message": "Document file path is missing."}), 422

    file_path = Path(filepath)
    if not file_path.exists():
        return jsonify({"message": "Document file is missing from storage."}), 404

    return send_file(
        file_path,
        as_attachment=False,
        download_name=document.get("filename", file_path.name),
    )


@documents_bp.delete("/documents/<document_id>")
@auth_required
def delete_document(document_id):
    document = delete_document_by_id(document_id, str(g.current_user["_id"]))
    if not document:
        return jsonify({"message": "Document not found."}), 404

    filepath = document.get("filepath")
    if filepath:
        try:
            Path(filepath).unlink(missing_ok=True)
        except OSError:
            current_app.logger.warning(
                "Deleted document record but could not remove file: %s",
                filepath,
            )

    return jsonify({"message": "Document deleted successfully."}), 200


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

    text = document.get("raw_text") or document.get("extracted_text") or document.get("cleaned_text", "")
    if not text:
        return jsonify({"message": "Document has no text to extract keywords from."}), 422

    keywords = extract_keywords(text, max_keywords=MAX_KEYWORDS)
    updated_document = update_document_keywords(
        document_id=document_id,
        user_id=str(g.current_user["_id"]),
        keywords=keywords,
    )

    return jsonify({"keywords": top_keywords(updated_document)}), 200


@documents_bp.post("/summarize/<document_id>")
@documents_bp.post("/documents/<document_id>/summarize")
@auth_required
def summarize_document(document_id):
    document = find_document_by_id(document_id, str(g.current_user["_id"]))
    if not document:
        return jsonify({"message": "Document not found."}), 404

    if document.get("summary_generated_at"):
        return jsonify({"message": "A summary has already been generated for this document."}), 409

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

    text = document.get("raw_text") or document.get("extracted_text") or document.get("cleaned_text", "")
    if not text:
        return jsonify({"message": "Document has no extracted text to process."}), 422

    keywords = extract_keywords(text, max_keywords=MAX_KEYWORDS)
    updated_document = update_document_keywords(
        document_id=document_id,
        user_id=str(g.current_user["_id"]),
        keywords=keywords,
    )

    return jsonify({"document": serialize_document_nlp(updated_document)}), 200
