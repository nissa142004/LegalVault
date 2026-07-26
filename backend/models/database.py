from flask import current_app, g
from pymongo import MongoClient
from pymongo.errors import PyMongoError


def init_mongo(app):
    mongo_uri = app.config["MONGO_URI"]
    if not mongo_uri:
        raise RuntimeError("MONGO_URI is required. Add it to backend/.env.")

    app.config["MONGO_CLIENT"] = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=5000,
    )
    app.config["MONGO_DB_NAME"] = app.config.get("MONGO_DB_NAME", "LegalVault")

    db = app.config["MONGO_CLIENT"][app.config["MONGO_DB_NAME"]]
    db.users.create_index("email", unique=True)
    db.users.create_index("created_at")
    db.documents.create_index("user_id")
    db.documents.create_index("uploaded_by")
    db.documents.create_index([("uploaded_by", 1), ("predicted_category", 1)])
    db.documents.create_index([("uploaded_by", 1), ("classification_status", 1)])
    db.documents.create_index([("uploaded_by", 1), ("matter_number", 1)])
    db.documents.create_index([("uploaded_by", 1), ("review_status", 1)])


def get_db():
    if "mongo_db" not in g:
        client = current_app.config["MONGO_CLIENT"]
        g.mongo_db = client[current_app.config["MONGO_DB_NAME"]]
    return g.mongo_db


def ping_mongo() -> bool:
    try:
        current_app.config["MONGO_CLIENT"].admin.command("ping")
        return True
    except PyMongoError:
        return False


def close_mongo(exception=None):
    g.pop("mongo_db", None)
