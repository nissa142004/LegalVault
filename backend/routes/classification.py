from flask import Blueprint, current_app, jsonify, request

from ml.classifier import DEFAULT_MODEL_PATH, ModelNotAvailableError, predict_category


classification_bp = Blueprint("classification", __name__)


@classification_bp.post("/predict-category")
def classify_legal_document():
    if not request.is_json:
        return jsonify({"message": "Request body must be JSON."}), 415

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"message": "Request body must be a JSON object."}), 400

    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        return jsonify({"message": "A non-empty 'text' string is required."}), 400
    if len(text) > current_app.config["CLASSIFIER_MAX_TEXT_LENGTH"]:
        return jsonify({"message": "Document text exceeds the allowed length."}), 413

    try:
        prediction = predict_category(
            text.strip(), current_app.config.get("CLASSIFIER_MODEL_PATH", DEFAULT_MODEL_PATH)
        )
    except ModelNotAvailableError as error:
        current_app.logger.error("Classifier unavailable: %s", error)
        return jsonify({"message": "Classification model is unavailable."}), 503

    return jsonify(prediction), 200
