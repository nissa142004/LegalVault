from functools import wraps

import jwt
from flask import g, jsonify, request

from models.user import find_user_by_id
from utils.jwt_utils import decode_access_token


def auth_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            return jsonify({"message": "Missing or invalid authorization header."}), 401

        token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            return jsonify({"message": "Missing token."}), 401

        try:
            payload = decode_access_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token."}), 401

        user = find_user_by_id(payload.get("sub", ""))
        if not user:
            return jsonify({"message": "User not found."}), 401

        g.current_user = user
        return view(*args, **kwargs)

    return wrapped
