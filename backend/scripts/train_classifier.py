from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATASET = Path.home() / "OneDrive" / "Desktop" / "data" / "legal_dataset.csv"
DEFAULT_MODEL = BACKEND_DIR / "ml" / "artifacts" / "legal_category_model.joblib"
DEFAULT_METRICS = BACKEND_DIR / "ml" / "artifacts" / "evaluation.json"
LABEL_MAP = {
    "Contract": "Contract",
    "Lease": "Lease",
    "Lease Agreement": "Lease",
    "Employment": "Employment",
    "Employment Agreement": "Employment",
    "Case Law": "Case Law",
    "Property": "Property",
    "Property Document": "Property",
}
EXPECTED_LABELS = {"Contract", "Lease", "Employment", "Case Law", "Property"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the LegalVault category classifier.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--model-output", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--metrics-output", type=Path, default=DEFAULT_METRICS)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def load_dataset(path: Path) -> tuple[pd.Series, pd.Series]:
    if not path.is_file():
        raise FileNotFoundError(f"Dataset not found: {path}")

    frame = pd.read_csv(path)
    required = {"text", "label"}
    if not required.issubset(frame.columns):
        raise ValueError("Dataset must contain 'text' and 'label' columns.")

    frame = frame[["text", "label"]].dropna()
    frame["text"] = frame["text"].astype(str).str.strip()
    frame["label"] = frame["label"].astype(str).str.strip().map(LABEL_MAP)
    frame = frame[(frame["text"] != "") & frame["label"].notna()]

    found_labels = set(frame["label"].unique())
    if found_labels != EXPECTED_LABELS:
        raise ValueError(
            f"Expected labels {sorted(EXPECTED_LABELS)}, found {sorted(found_labels)}."
        )
    if frame["label"].value_counts().min() < 2:
        raise ValueError("Each category needs at least two documents for stratified evaluation.")
    return frame["text"], frame["label"]


def main() -> int:
    args = parse_args()
    texts, labels = load_dataset(args.dataset)
    x_train, x_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=labels,
    )

    pipeline = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=2,
                    sublinear_tf=True,
                ),
            ),
            ("classifier", MultinomialNB(alpha=0.5)),
        ]
    )
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    accuracy = float(accuracy_score(y_test, predictions))
    ordered_labels = sorted(EXPECTED_LABELS)
    trained_at = datetime.now(timezone.utc).isoformat()

    metrics = {
        "accuracy": accuracy,
        "classification_report": classification_report(
            y_test, predictions, labels=ordered_labels, output_dict=True, zero_division=0
        ),
        "confusion_matrix": confusion_matrix(
            y_test, predictions, labels=ordered_labels
        ).tolist(),
        "labels": ordered_labels,
        "dataset_rows": len(texts),
        "training_rows": len(x_train),
        "test_rows": len(x_test),
        "random_state": args.random_state,
        "trained_at": trained_at,
    }
    artifact = {
        "pipeline": pipeline,
        "model_version": trained_at,
        "labels": ordered_labels,
        "metrics": {"accuracy": accuracy},
        "sklearn_version": sklearn.__version__,
    }

    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, args.model_output)
    args.metrics_output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Trained on {len(x_train)} documents; tested on {len(x_test)} documents.")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Model: {args.model_output.resolve()}")
    print(f"Metrics: {args.metrics_output.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (FileNotFoundError, ValueError) as error:
        print(f"Training failed: {error}", file=sys.stderr)
        sys.exit(1)
