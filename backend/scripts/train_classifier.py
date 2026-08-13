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
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
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


def print_evaluation(
    *,
    labels: pd.Series,
    y_test: pd.Series,
    train_predictions: pd.Series,
    test_predictions: pd.Series,
    ordered_labels: list[str],
) -> dict[str, object]:
    train_accuracy = float(accuracy_score(labels.loc[train_predictions.index], train_predictions))
    test_accuracy = float(accuracy_score(y_test, test_predictions))
    macro_precision = float(precision_score(y_test, test_predictions, average="macro", zero_division=0))
    macro_recall = float(recall_score(y_test, test_predictions, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_test, test_predictions, average="macro", zero_division=0))
    weighted_precision = float(
        precision_score(y_test, test_predictions, average="weighted", zero_division=0)
    )
    weighted_recall = float(
        recall_score(y_test, test_predictions, average="weighted", zero_division=0)
    )
    weighted_f1 = float(f1_score(y_test, test_predictions, average="weighted", zero_division=0))
    correct = int((y_test == test_predictions).sum())
    incorrect = int(len(y_test) - correct)
    matrix = confusion_matrix(y_test, test_predictions, labels=ordered_labels)
    report_text = classification_report(
        y_test,
        test_predictions,
        labels=ordered_labels,
        target_names=ordered_labels,
        digits=2,
        zero_division=0,
    )

    separator = "=" * 60
    subsection = "-" * 60
    print(f"\n{separator}\nLEGALVAULT MODEL EVALUATION\n{separator}\n")
    print(f"Dataset Information\n{subsection}")
    print(f"Total samples       : {len(labels)}")
    print(f"Training samples    : {len(train_predictions)}")
    print(f"Testing samples     : {len(y_test)}")
    print(f"Number of classes   : {len(ordered_labels)}\n")
    print("Classes and sample counts:")
    class_counts = labels.value_counts().reindex(ordered_labels)
    for label, count in class_counts.items():
        print(f"- {label}: {count}")

    print(f"\nModel\n{subsection}")
    print("Algorithm           : Multinomial Naive Bayes")
    print("Features            : TF-IDF")
    print("Split               : 80% training / 20% independent testing (stratified)")
    print(f"\nTraining Accuracy   : {train_accuracy:.2%}")
    print(f"Testing Accuracy    : {test_accuracy:.2%}")

    print(f"\nOverall Test Metrics (macro average)\n{subsection}")
    print(f"Precision           : {macro_precision:.2%}")
    print(f"Recall              : {macro_recall:.2%}")
    print(f"F1-score            : {macro_f1:.2%}")

    print(f"\nMacro Average\n{subsection}")
    print(f"Precision           : {macro_precision:.2%}")
    print(f"Recall              : {macro_recall:.2%}")
    print(f"F1-score            : {macro_f1:.2%}")

    print(f"\nWeighted Average\n{subsection}")
    print(f"Precision           : {weighted_precision:.2%}")
    print(f"Recall              : {weighted_recall:.2%}")
    print(f"F1-score            : {weighted_f1:.2%}")

    print(f"\nClassification Report\n{subsection}")
    print(report_text)
    print(f"Confusion Matrix (rows=true, columns=predicted)\n{subsection}")
    print(pd.DataFrame(matrix, index=ordered_labels, columns=ordered_labels).to_string())
    print(f"\nCorrect Predictions   : {correct}")
    print(f"Incorrect Predictions : {incorrect}")
    print(f"\n{separator}\nEVALUATION COMPLETED\n{separator}")

    return {
        "training_accuracy": train_accuracy,
        "test_accuracy": test_accuracy,
        "precision": macro_precision,
        "recall": macro_recall,
        "f1_score": macro_f1,
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1_score": macro_f1,
        "weighted_precision": weighted_precision,
        "weighted_recall": weighted_recall,
        "weighted_f1_score": weighted_f1,
        "correct_predictions": correct,
        "incorrect_predictions": incorrect,
        "confusion_matrix": matrix.tolist(),
        "class_distribution": {str(label): int(count) for label, count in class_counts.items()},
    }


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
    train_predictions = pd.Series(pipeline.predict(x_train), index=y_train.index)
    predictions = pd.Series(pipeline.predict(x_test), index=y_test.index)
    ordered_labels = sorted(EXPECTED_LABELS)
    trained_at = datetime.now(timezone.utc).isoformat()

    evaluation = print_evaluation(
        labels=labels,
        y_test=y_test,
        train_predictions=train_predictions,
        test_predictions=predictions,
        ordered_labels=ordered_labels,
    )

    metrics = {
        "accuracy": evaluation["test_accuracy"],
        **evaluation,
        "classification_report": classification_report(
            y_test, predictions, labels=ordered_labels, output_dict=True, zero_division=0
        ),
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
        "metrics": {
            "accuracy": evaluation["test_accuracy"],
            "training_accuracy": evaluation["training_accuracy"],
        },
        "sklearn_version": sklearn.__version__,
    }

    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, args.model_output)
    args.metrics_output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Model artifact       : {args.model_output.resolve()}")
    print(f"Metrics artifact     : {args.metrics_output.resolve()}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (FileNotFoundError, ValueError) as error:
        print(f"Training failed: {error}", file=sys.stderr)
        sys.exit(1)
