import re
from datetime import datetime, timezone

from bson import ObjectId

from models.database import get_db
from utils.text_extraction import get_stopwords

MAX_KEYWORDS = 10
MIN_KEYWORD_LENGTH = 3


def documents_collection():
    return get_db().documents


def top_keywords(document: dict) -> list[str]:
    stopword_set = get_stopwords()
    keywords = []
    seen = set()

    for keyword in document.get("keywords") or []:
        words = re.findall(r"[a-zA-Z][a-zA-Z0-9']*", str(keyword).lower())
        clean_words = [
            word for word in words
            if len(word) >= MIN_KEYWORD_LENGTH and word not in stopword_set
        ]
        phrase = " ".join(clean_words[:4])
        if not phrase or phrase in seen:
            continue

        keywords.append(phrase)
        seen.add(phrase)
        if len(keywords) == MAX_KEYWORDS:
            return keywords

    return keywords


def serialize_document(document: dict) -> dict:
    upload_date = document["upload_date"]
    if upload_date.tzinfo is None:
        upload_date = upload_date.replace(tzinfo=timezone.utc)

    predicted_category = (
        document.get("predicted_category")
        or document.get("category")
        or "Uncategorized"
    )
    confidence_score = document.get("confidence_score", document.get("category_confidence"))

    return {
        "id": str(document["_id"]),
        "filename": document["filename"],
        "filepath": document.get("filepath", ""),
        "uploaded_by": document.get("uploaded_by", document.get("user_id", "")),
        "upload_date": upload_date.isoformat(),
        "has_raw_text": bool(document.get("raw_text") or document.get("extracted_text")),
        "has_nlp_results": bool(document.get("keywords") or document.get("summary")),
        "category": predicted_category,
        "predicted_category": predicted_category,
        "confidence_score": confidence_score,
        "category_confidence": confidence_score,
        "classification_status": document.get("classification_status", "assigned"),
        "classification_warning": document.get("classification_warning"),
        "top_predictions": document.get("top_predictions", []),
    }


def serialize_document_text(document: dict) -> dict:
    serialized = serialize_document(document)
    serialized["raw_text"] = document.get("raw_text", document.get("extracted_text", ""))
    serialized["cleaned_text"] = document.get("cleaned_text", "")
    serialized["keywords"] = top_keywords(document)
    serialized["summary"] = document.get("summary", "")

    return serialized


def serialize_document_nlp(document: dict) -> dict:
    serialized = serialize_document(document)
    serialized["keywords"] = top_keywords(document)
    serialized["summary"] = document.get("summary", "")

    return serialized


def create_document(
    filename: str,
    filepath: str,
    uploaded_by: str,
    raw_text: str = "",
    cleaned_text: str = "",
    predicted_category: str | None = None,
    confidence_score: float | None = None,
    keywords: list[str] | None = None,
    summary: str = "",
    classification_status: str = "assigned",
    classification_warning: str | None = None,
    top_predictions: list[dict] | None = None,
    category: str | None = None,
    category_confidence: float | None = None,
) -> dict:
    now = datetime.now(timezone.utc)
    final_confidence = confidence_score if confidence_score is not None else category_confidence
    final_category = predicted_category or category or "Uncategorized"
    document = {
        "filename": filename,
        "filepath": filepath,
        "uploaded_by": uploaded_by,
        "upload_date": now,
        "updated_at": now,
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
        "predicted_category": final_category,
        "confidence_score": final_confidence,
        "category": final_category,
        "category_confidence": final_confidence,
        "classification_status": classification_status,
        "classification_warning": classification_warning,
        "top_predictions": top_predictions or [],
        "keywords": keywords or [],
        "summary": summary,
    }
    result = documents_collection().insert_one(document)
    document["_id"] = result.inserted_id

    return document


def find_documents_by_user(user_id: str) -> list[dict]:
    return list(
        documents_collection()
        .find({"$or": [{"uploaded_by": user_id}, {"user_id": user_id}]})
        .sort("upload_date", -1)
    )


def find_document_by_id(document_id: str, user_id: str) -> dict | None:
    if not ObjectId.is_valid(document_id):
        return None

    return documents_collection().find_one(
        {
            "_id": ObjectId(document_id),
            "$or": [{"uploaded_by": user_id}, {"user_id": user_id}],
        }
    )


def delete_document_by_id(document_id: str, user_id: str) -> dict | None:
    document = find_document_by_id(document_id, user_id)
    if not document:
        return None

    documents_collection().delete_one({"_id": document["_id"]})

    return document


def update_document_nlp(document_id: str, user_id: str, keywords: list[str], summary: str):
    if not ObjectId.is_valid(document_id):
        return None

    documents_collection().update_one(
        {
            "_id": ObjectId(document_id),
            "$or": [{"uploaded_by": user_id}, {"user_id": user_id}],
        },
        {
            "$set": {
                "keywords": keywords,
                "summary": summary,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    return find_document_by_id(document_id, user_id)


def update_document_keywords(
    document_id: str,
    user_id: str,
    keywords: list[str],
) -> dict | None:
    if not ObjectId.is_valid(document_id):
        return None

    documents_collection().update_one(
        {
            "_id": ObjectId(document_id),
            "$or": [{"uploaded_by": user_id}, {"user_id": user_id}],
        },
        {"$set": {"keywords": keywords, "updated_at": datetime.now(timezone.utc)}},
    )

    return find_document_by_id(document_id, user_id)


def update_document_summary(
    document_id: str,
    user_id: str,
    summary: str,
    summary_sentence_count: int,
) -> dict | None:
    if not ObjectId.is_valid(document_id):
        return None

    documents_collection().update_one(
        {
            "_id": ObjectId(document_id),
            "$or": [{"uploaded_by": user_id}, {"user_id": user_id}],
        },
        {
            "$set": {
                "summary": summary,
                "summary_sentence_count": summary_sentence_count,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    return find_document_by_id(document_id, user_id)


def update_document_text(
    document_id: str,
    user_id: str,
    raw_text: str,
    cleaned_text: str,
) -> dict | None:
    if not ObjectId.is_valid(document_id):
        return None

    documents_collection().update_one(
        {
            "_id": ObjectId(document_id),
            "$or": [{"uploaded_by": user_id}, {"user_id": user_id}],
        },
        {
            "$set": {
                "raw_text": raw_text,
                "cleaned_text": cleaned_text,
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )

    return find_document_by_id(document_id, user_id)
