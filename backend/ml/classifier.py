from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib


DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "legal_category_model.joblib"
LOW_CONFIDENCE_THRESHOLD = 0.50


class ModelNotAvailableError(RuntimeError):
    """Raised when the trained classifier artifact cannot be loaded."""


@lru_cache(maxsize=4)
def load_model(model_path: str) -> dict[str, Any]:
    path = Path(model_path)
    if not path.is_file():
        raise ModelNotAvailableError(
            f"Classifier model not found at {path}. Run scripts/train_classifier.py first."
        )

    artifact = joblib.load(path)
    if not isinstance(artifact, dict) or "pipeline" not in artifact:
        raise ModelNotAvailableError(f"Invalid classifier artifact at {path}.")
    return artifact


def predict_category(
    text: str,
    model_path: str | Path = DEFAULT_MODEL_PATH,
    low_confidence_threshold: float = LOW_CONFIDENCE_THRESHOLD,
) -> dict[str, Any]:
    artifact = load_model(str(Path(model_path).resolve()))
    pipeline = artifact["pipeline"]
    probabilities = pipeline.predict_proba([text])[0]
    classes = pipeline.classes_
    best_index = int(probabilities.argmax())
    confidence = float(probabilities[best_index])
    ranked_predictions = [
        {
            "category": str(label),
            "probability": round(float(score), 6),
            "percentage": round(float(score) * 100, 2),
        }
        for label, score in sorted(
            zip(classes, probabilities), key=lambda item: item[1], reverse=True
        )
    ]
    is_low_confidence = confidence < low_confidence_threshold

    return {
        "category": str(classes[best_index]),
        "predicted_category": str(classes[best_index]),
        "confidence": round(confidence, 6),
        "confidence_score": round(confidence, 6),
        "confidence_percentage": round(confidence * 100, 2),
        "is_low_confidence": is_low_confidence,
        "warning": (
            f"Low confidence prediction ({round(confidence * 100, 2)}%). "
            "Manual review recommended."
            if is_low_confidence
            else None
        ),
        "top_predictions": ranked_predictions[:3],
        "probabilities": {
            item["category"]: item["probability"] for item in ranked_predictions
        },
        "model_version": artifact.get("model_version", "unknown"),
    }
