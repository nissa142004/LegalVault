from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from models.database import close_mongo, init_mongo
from routes.auth import auth_bp
from routes.documents import documents_bp
from routes.protected import protected_bp
from routes.status import status_bp
from utils.config import Config
from utils.error_handlers import register_error_handlers


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(
        app,
        resources={
            r"/api/*": {"origins": app.config["CORS_ORIGINS"]},
            r"/auth/*": {"origins": app.config["CORS_ORIGINS"]},
            r"/documents.*": {"origins": app.config["CORS_ORIGINS"]},
            r"/extract-keywords/.*": {"origins": app.config["CORS_ORIGINS"]},
            r"/search": {"origins": app.config["CORS_ORIGINS"]},
            r"/upload": {"origins": app.config["CORS_ORIGINS"]},
        },
    )

    jwt = JWTManager(app)
    init_mongo(app)
    app.register_blueprint(status_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(protected_bp)
    app.register_blueprint(documents_bp)
    register_error_handlers(app)
    app.teardown_appcontext(close_mongo)

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"message": "Token has expired.", "error": "token_expired"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"message": "Invalid authentication token.", "error": "token_invalid"}), 422

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"message": "Authorization token is required.", "error": "token_missing"}), 401

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
        use_reloader=False,
    )
