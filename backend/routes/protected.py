from flask import Blueprint, g, jsonify

from models.user import serialize_user
from utils.auth_middleware import auth_required

protected_bp = Blueprint("protected", __name__)


@protected_bp.get("/protected")
@auth_required
def protected():
    return jsonify(
        {
            "message": "JWT token is valid.",
            "user": serialize_user(g.current_user),
        }
    ), 200
