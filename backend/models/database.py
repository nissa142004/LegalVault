from flask import current_app, g
from pymongo import MongoClient
from pymongo.errors import PyMongoError


def init_mongo(app):
    """Create the MongoDB client and prepare indexes used by the API."""
    mongo_uri = app.config["MONGO_URI"]
    if not mongo_uri:
        raise RuntimeError("MONGO_URI is required. Add it to backend/.env.")

    app.config["MONGO_CLIENT"] = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=5000,
    )
    app.config["MONGO_DB_NAME"] = app.config.get("MONGO_DB_NAME", "LegalVault")

    db = app.config["MONGO_CLIENT"][app.config["MONGO_DB_NAME"]]
    # Indexes keep login and user-specific document lookups fast and reliable.
    db.users.create_index("email", unique=True)
    db.documents.create_index("user_id")
    db.documents.create_index("uploaded_by")


def get_db():
    """Return the request-scoped MongoDB database handle."""
    if "mongo_db" not in g:
        client = current_app.config["MONGO_CLIENT"]
        g.mongo_db = client[current_app.config["MONGO_DB_NAME"]]
    return g.mongo_db


def ping_mongo() -> bool:
    """Health-check helper used by /api/status."""
    try:
        current_app.config["MONGO_CLIENT"].admin.command("ping")
        return True
    except PyMongoError:
        return False


def close_mongo(exception=None):
    """Clear the request-scoped database handle after each Flask app context."""
    g.pop("mongo_db", None)
