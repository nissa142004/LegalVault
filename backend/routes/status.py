from flask import Blueprint, jsonify

from models.database import ping_mongo

status_bp = Blueprint("status", __name__)


@status_bp.get("/status")
def status():
    mongo_connected = ping_mongo()

    return jsonify(
        {
            "service": "LegalVault Backend",
            "status": "ok" if mongo_connected else "degraded",
            "mongodb": "connected" if mongo_connected else "unavailable",
        }
    ), 200 if mongo_connected else 503
