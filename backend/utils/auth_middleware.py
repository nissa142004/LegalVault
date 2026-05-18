from functools import wraps

from flask import g, jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from models.user import find_user_by_id


def auth_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        verify_jwt_in_request()
        user = find_user_by_id(get_jwt_identity())
        if not user:
            return jsonify({"message": "User not found."}), 401

        g.current_user = user
        return view(*args, **kwargs)

    return wrapped
