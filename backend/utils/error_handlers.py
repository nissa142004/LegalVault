from http import HTTPStatus

from flask import jsonify
from pymongo.errors import PyMongoError
from werkzeug.exceptions import HTTPException


def register_error_handlers(app):
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify(
            {
                "message": error.description or HTTPStatus(error.code).phrase,
                "status_code": error.code,
            }
        ), error.code

    @app.errorhandler(PyMongoError)
    def handle_mongo_error(error):
        app.logger.exception("MongoDB error: %s", error)
        return jsonify(
            {
                "message": "A database error occurred.",
                "status_code": 503,
            }
        ), 503

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception("Unexpected error: %s", error)
        return jsonify(
            {
                "message": "An unexpected server error occurred.",
                "status_code": 500,
            }
        ), 500
