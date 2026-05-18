from flask import Blueprint, g, jsonify, request
from flask_jwt_extended import create_access_token
from pymongo.errors import DuplicateKeyError

from models.user import create_user, find_user_by_email, serialize_user
from utils.auth_middleware import auth_required
from utils.passwords import check_password, hash_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"message": "Name, email, and password are required."}), 400

    if len(password) < 8:
        return jsonify({"message": "Password must be at least 8 characters."}), 400

    if find_user_by_email(email):
        return jsonify({"message": "User with this email already exists."}), 409

    try:
        user = create_user(name, email, hash_password(password))
    except DuplicateKeyError:
        return jsonify({"message": "User with this email already exists."}), 409

    token = create_access_token(identity=str(user["_id"]))

    return jsonify({"token": token, "user": serialize_user(user)}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").lower().strip()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Email and password are required."}), 400

    user = find_user_by_email(email)
    if not user or not check_password(password, user["password"]):
        return jsonify({"message": "Invalid email or password."}), 401

    token = create_access_token(identity=str(user["_id"]))

    return jsonify({"token": token, "user": serialize_user(user)}), 200


@auth_bp.get("/me")
@auth_required
def me():
    return jsonify({"user": serialize_user(g.current_user)}), 200
