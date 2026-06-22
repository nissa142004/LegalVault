from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib


DEFAULT_MODEL_PATH = Path(__file__).resolve().parent / "artifacts" / "legal_category_model.joblib"


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


def predict_category(text: str, model_path: str | Path = DEFAULT_MODEL_PATH) -> dict[str, Any]:
    artifact = load_model(str(Path(model_path).resolve()))
    pipeline = artifact["pipeline"]
    probabilities = pipeline.predict_proba([text])[0]
    classes = pipeline.classes_
    best_index = int(probabilities.argmax())

    return {
        "category": str(classes[best_index]),
        "confidence": round(float(probabilities[best_index]), 6),
        "probabilities": {
            str(label): round(float(score), 6)
            for label, score in sorted(
                zip(classes, probabilities), key=lambda item: item[1], reverse=True
            )
        },
        "model_version": artifact.get("model_version", "unknown"),
    }
