from datetime import datetime, timezone

from bson import ObjectId

from models.database import get_db


def users_collection():
    """Return the user collection used by this module."""
    return get_db().users


def serialize_user(user: dict | None) -> dict | None:
    """Return safe user fields without exposing the password hash."""
    if not user:
        return None

    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "phone": user.get("phone", ""),
        "organization": user.get("organization", ""),
        "job_title": user.get("job_title", ""),
        "jurisdiction": user.get("jurisdiction", ""),
        "professional_id": user.get("professional_id", ""),
    }


def find_user_by_email(email: str) -> dict | None:
    """Look up an account by its normalized email address."""
    return users_collection().find_one({"email": email.lower().strip()})


def find_user_by_id(user_id: str) -> dict | None:
    """Look up an account when the supplied ID is valid."""
    if not ObjectId.is_valid(user_id):
        return None

    return users_collection().find_one({"_id": ObjectId(user_id)})


def create_user(
    name: str,
    email: str,
    hashed_password: str,
    role: str = "user",
    profile: dict | None = None,
) -> dict:
    """Create and return a new user record."""
    profile = profile or {}
    user = {
        "name": name.strip(),
        "email": email.lower().strip(),
        "password": hashed_password,
        "role": role,
        "phone": profile.get("phone", "").strip(),
        "organization": profile.get("organization", "").strip(),
        "job_title": profile.get("job_title", "").strip(),
        "jurisdiction": profile.get("jurisdiction", "").strip(),
        "professional_id": profile.get("professional_id", "").strip(),
        "created_at": datetime.now(timezone.utc),
        "password_changed_at": None,
    }
    result = users_collection().insert_one(user)
    user["_id"] = result.inserted_id

    return user


def update_user_password(user_id: str, hashed_password: str) -> bool:
    """Store a new password hash for an existing user."""
    if not ObjectId.is_valid(user_id):
        return False
    result = users_collection().update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": hashed_password, "password_changed_at": datetime.now(timezone.utc)}},
    )
    return result.modified_count == 1


def update_user_profile(user_id: str, profile: dict) -> dict | None:
    """Update only the profile fields users are allowed to edit."""
    if not ObjectId.is_valid(user_id):
        return None
    allowed_fields = ("name", "phone", "organization", "job_title", "jurisdiction", "professional_id")
    updates = {field: str(profile.get(field) or "").strip() for field in allowed_fields}
    updates["updated_at"] = datetime.now(timezone.utc)
    users_collection().update_one({"_id": ObjectId(user_id)}, {"$set": updates})
    return find_user_by_id(user_id)
