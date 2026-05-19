import re

from flask import Blueprint, current_app, g, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt
from pymongo.errors import DuplicateKeyError

from models.user import create_user, find_user_by_email, serialize_user
from utils.auth_middleware import auth_required
from utils.passwords import check_password, hash_password

auth_bp = Blueprint("auth", __name__)

ALLOWED_ROLES = {"user", "admin"}
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_auth_payload(data: dict, require_name: bool = False) -> tuple[dict, str | None]:
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""
    role = (data.get("role") or "user").lower().strip()

    if require_name and not name:
        return {}, "Name is required."

    if require_name and (len(name) < 2 or len(name) > 80):
        return {}, "Name must be between 2 and 80 characters."

    if not email or not EMAIL_PATTERN.match(email):
        return {}, "A valid email address is required."

    if not password:
        return {}, "Password is required."

    if require_name and len(password) < 8:
        return {}, "Password must be at least 8 characters."

    if require_name and not re.search(r"[A-Za-z]", password):
        return {}, "Password must include at least one letter."

    if require_name and not re.search(r"\d", password):
        return {}, "Password must include at least one number."

    if role not in ALLOWED_ROLES:
        return {}, "Role must be either user or admin."

    return {
        "name": name,
        "email": email,
        "password": password,
        "role": role,
    }, None


def create_user_token(user: dict) -> str:
    return create_access_token(
        identity=str(user["_id"]),
        additional_claims={"role": user.get("role", "user")},
    )


def admin_registration_allowed(data: dict) -> bool:
    expected_key = current_app.config.get("ADMIN_REGISTRATION_KEY")
    submitted_key = data.get("admin_key")

    return bool(expected_key and submitted_key and submitted_key == expected_key)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    payload, error = validate_auth_payload(data, require_name=True)
    if error:
        return jsonify({"message": error}), 400

    if payload["role"] == "admin" and not admin_registration_allowed(data):
        return jsonify({"message": "Admin registration is not allowed."}), 403

    if find_user_by_email(payload["email"]):
        return jsonify({"message": "User with this email already exists."}), 409

    try:
        user = create_user(
            payload["name"],
            payload["email"],
            hash_password(payload["password"]),
            role=payload["role"],
        )
    except DuplicateKeyError:
        return jsonify({"message": "User with this email already exists."}), 409

    token = create_user_token(user)

    return jsonify({"token": token, "user": serialize_user(user)}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    payload, error = validate_auth_payload(data)
    if error:
        return jsonify({"message": error}), 400

    user = find_user_by_email(payload["email"])
    if not user or not check_password(payload["password"], user["password"]):
        return jsonify({"message": "Invalid email or password."}), 401

    token = create_user_token(user)

    return jsonify({"token": token, "user": serialize_user(user)}), 200


@auth_bp.get("/me")
@auth_required
def me():
    return jsonify({"user": serialize_user(g.current_user)}), 200


@auth_bp.get("/profile")
@auth_required
def profile():
    claims = get_jwt()
    user = serialize_user(g.current_user)
    user["role"] = claims.get("role", user.get("role", "user"))

    return jsonify({"user": user}), 200
