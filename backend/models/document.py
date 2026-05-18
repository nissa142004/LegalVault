from datetime import datetime, timezone

from bson import ObjectId

from models.database import get_db


def documents_collection():
    return get_db().documents


def serialize_document(document: dict) -> dict:
    upload_date = document["upload_date"]
    if upload_date.tzinfo is None:
        upload_date = upload_date.replace(tzinfo=timezone.utc)

    return {
        "id": str(document["_id"]),
        "filename": document["filename"],
        "filepath": document.get("filepath", ""),
        "uploaded_by": document.get("uploaded_by", document.get("user_id", "")),
        "upload_date": upload_date.isoformat(),
        "has_raw_text": bool(document.get("raw_text") or document.get("extracted_text")),
        "has_nlp_results": bool(document.get("keywords") or document.get("summary")),
    }


def serialize_document_text(document: dict) -> dict:
    serialized = serialize_document(document)
    serialized["raw_text"] = document.get("raw_text", document.get("extracted_text", ""))
    serialized["cleaned_text"] = document.get("cleaned_text", "")

    return serialized


def serialize_document_nlp(document: dict) -> dict:
    serialized = serialize_document(document)
    serialized["keywords"] = document.get("keywords", [])
    serialized["summary"] = document.get("summary", "")

    return serialized


def create_document(
    filename: str,
    filepath: str,
    uploaded_by: str,
    raw_text: str = "",
    cleaned_text: str = "",
) -> dict:
    document = {
        "filename": filename,
        "filepath": filepath,
        "uploaded_by": uploaded_by,
        "upload_date": datetime.now(timezone.utc),
        "raw_text": raw_text,
        "cleaned_text": cleaned_text,
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


def update_document_nlp(document_id: str, user_id: str, keywords: list[str], summary: str):
    if not ObjectId.is_valid(document_id):
        return None

    documents_collection().update_one(
        {
            "_id": ObjectId(document_id),
            "$or": [{"uploaded_by": user_id}, {"user_id": user_id}],
        },
        {"$set": {"keywords": keywords, "summary": summary}},
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
        {"$set": {"keywords": keywords}},
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
        {"$set": {"raw_text": raw_text, "cleaned_text": cleaned_text}},
    )

    return find_document_by_id(document_id, user_id)
