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
        "user_id": document["user_id"],
        "upload_date": upload_date.isoformat(),
        "has_extracted_text": bool(document.get("extracted_text")),
        "has_nlp_results": bool(document.get("keywords") or document.get("summary")),
    }


def serialize_document_text(document: dict) -> dict:
    serialized = serialize_document(document)
    serialized["extracted_text"] = document.get("extracted_text", "")
    serialized["cleaned_text"] = document.get("cleaned_text", "")

    return serialized


def serialize_document_nlp(document: dict) -> dict:
    serialized = serialize_document(document)
    serialized["keywords"] = document.get("keywords", [])
    serialized["summary"] = document.get("summary", "")

    return serialized


def create_document(
    filename: str,
    user_id: str,
    extracted_text: str = "",
    cleaned_text: str = "",
) -> dict:
    document = {
        "filename": filename,
        "user_id": user_id,
        "upload_date": datetime.now(timezone.utc),
        "extracted_text": extracted_text,
        "cleaned_text": cleaned_text,
    }
    result = documents_collection().insert_one(document)
    document["_id"] = result.inserted_id

    return document


def find_documents_by_user(user_id: str) -> list[dict]:
    return list(
        documents_collection()
        .find({"user_id": user_id})
        .sort("upload_date", -1)
    )


def find_document_by_id(document_id: str, user_id: str) -> dict | None:
    if not ObjectId.is_valid(document_id):
        return None

    return documents_collection().find_one(
        {"_id": ObjectId(document_id), "user_id": user_id}
    )


def update_document_nlp(document_id: str, user_id: str, keywords: list[str], summary: str):
    if not ObjectId.is_valid(document_id):
        return None

    documents_collection().update_one(
        {"_id": ObjectId(document_id), "user_id": user_id},
        {"$set": {"keywords": keywords, "summary": summary}},
    )

    return find_document_by_id(document_id, user_id)
