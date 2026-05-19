from bson import ObjectId

from models.database import get_db


def users_collection():
    return get_db().users


def serialize_user(user: dict | None) -> dict | None:
    if not user:
        return None

    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "user"),
    }


def find_user_by_email(email: str) -> dict | None:
    return users_collection().find_one({"email": email.lower().strip()})


def find_user_by_id(user_id: str) -> dict | None:
    if not ObjectId.is_valid(user_id):
        return None

    return users_collection().find_one({"_id": ObjectId(user_id)})


def create_user(
    name: str,
    email: str,
    hashed_password: str,
    role: str = "user",
) -> dict:
    user = {
        "name": name.strip(),
        "email": email.lower().strip(),
        "password": hashed_password,
        "role": role,
    }
    result = users_collection().insert_one(user)
    user["_id"] = result.inserted_id

    return user
