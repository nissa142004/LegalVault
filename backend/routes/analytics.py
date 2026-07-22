from collections import Counter
from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, g, jsonify

from ml.classifier import ModelNotAvailableError, predict_category
from models.document import find_documents_by_user, serialize_document
from utils.auth_middleware import auth_required


analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/analytics/dashboard")
@auth_required
def dashboard_analytics():
    documents = find_documents_by_user(str(g.current_user["_id"]))
    category_counts = Counter()
    extracted_count = 0
    processed_count = 0

    for document in documents:
        raw_text = document.get("raw_text") or document.get("extracted_text", "")
        if raw_text:
            extracted_count += 1
        if document.get("summary_generated_at"):
            processed_count += 1

        category = document.get("category")
        if not category and raw_text:
            try:
                category = predict_category(
                    raw_text, current_app.config["CLASSIFIER_MODEL_PATH"]
                )["category"]
            except ModelNotAvailableError:
                category = "Uncategorized"
        category_counts[category or "Uncategorized"] += 1

    total = len(documents)
    categories = [
        {
            "category": category,
            "count": count,
            "percentage": round((count / total * 100) if total else 0, 1),
        }
        for category, count in sorted(
            category_counts.items(), key=lambda item: (-item[1], item[0])
        )
    ]

    today = datetime.now(timezone.utc).date()
    upload_counts = Counter()
    for document in documents:
        uploaded = document.get("upload_date")
        if uploaded:
            upload_counts[uploaded.date().isoformat()] += 1
    uploads_by_day = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        uploads_by_day.append(
            {"date": day.isoformat(), "count": upload_counts[day.isoformat()]}
        )

    return jsonify(
        {
            "total_documents": total,
            "categories": categories,
            "recent_uploads": [serialize_document(doc) for doc in documents[:5]],
            "processing": {
                "text_extracted": extracted_count,
                "ai_processed": processed_count,
                "pending": total - processed_count,
                "completion_rate": round(
                    (processed_count / total * 100) if total else 0, 1
                ),
            },
            "uploads_by_day": uploads_by_day,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    ), 200
