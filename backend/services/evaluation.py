from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def load_classification_metrics(metrics_path: str | Path) -> dict[str, Any]:
    path = Path(metrics_path)
    if not path.is_file():
        return {"available": False, "message": "Classification metrics artifact not found."}

    metrics = json.loads(path.read_text(encoding="utf-8"))
    report = metrics.get("classification_report", {})
    macro = report.get("macro avg", {})
    weighted = report.get("weighted avg", {})

    return {
        "available": True,
        "accuracy": metrics.get("accuracy"),
        "precision": macro.get("precision"),
        "recall": macro.get("recall"),
        "f1_score": macro.get("f1-score"),
        "weighted_precision": weighted.get("precision"),
        "weighted_recall": weighted.get("recall"),
        "weighted_f1_score": weighted.get("f1-score"),
        "classification_report": report,
        "confusion_matrix": metrics.get("confusion_matrix", []),
        "labels": metrics.get("labels", []),
        "dataset_rows": metrics.get("dataset_rows"),
        "training_rows": metrics.get("training_rows"),
        "test_rows": metrics.get("test_rows"),
        "trained_at": metrics.get("trained_at"),
    }


def summarization_metrics(documents: list[dict]) -> dict[str, Any]:
    evaluated = []
    compression_ratios = []
    rouge_1_scores = []
    rouge_l_scores = []

    for document in documents:
        source = document.get("raw_text") or document.get("extracted_text") or ""
        generated = document.get("summary") or ""
        if not source.strip() or not generated.strip():
            continue

        compression = _compression_ratio(source, generated)
        compression_ratios.append(compression)

        reference = document.get("reference_summary") or document.get("gold_summary")
        rouge_1 = None
        rouge_l = None
        if reference:
            rouge_1 = _rouge_n(reference, generated, n=1)
            rouge_l = _rouge_l(reference, generated)
            rouge_1_scores.append(rouge_1)
            rouge_l_scores.append(rouge_l)

        evaluated.append(
            {
                "document_id": str(document["_id"]),
                "filename": document.get("filename"),
                "rouge_1": rouge_1,
                "rouge_l": rouge_l,
                "compression_ratio": compression,
            }
        )

    return {
        "available": bool(evaluated),
        "rouge_1": _average(rouge_1_scores),
        "rouge_l": _average(rouge_l_scores),
        "compression_ratio": _average(compression_ratios),
        "evaluated_documents": len(evaluated),
        "reference_summary_documents": len(rouge_1_scores),
        "documents": evaluated,
        "note": (
            "ROUGE needs reference_summary or gold_summary fields. "
            "Compression ratio is available for generated summaries."
        ),
    }


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def _compression_ratio(source: str, summary: str) -> float:
    source_tokens = _tokens(source)
    summary_tokens = _tokens(summary)
    if not source_tokens:
        return 0.0
    return round(len(summary_tokens) / len(source_tokens), 4)


def _rouge_n(reference: str, candidate: str, n: int) -> float:
    reference_tokens = _tokens(reference)
    candidate_tokens = _tokens(candidate)
    if len(reference_tokens) < n or len(candidate_tokens) < n:
        return 0.0

    reference_ngrams = Counter(
        tuple(reference_tokens[index:index + n])
        for index in range(len(reference_tokens) - n + 1)
    )
    candidate_ngrams = Counter(
        tuple(candidate_tokens[index:index + n])
        for index in range(len(candidate_tokens) - n + 1)
    )
    overlap = sum((reference_ngrams & candidate_ngrams).values())
    return round(overlap / max(sum(reference_ngrams.values()), 1), 4)


def _rouge_l(reference: str, candidate: str) -> float:
    reference_tokens = _tokens(reference)
    candidate_tokens = _tokens(candidate)
    if not reference_tokens or not candidate_tokens:
        return 0.0

    previous = [0] * (len(candidate_tokens) + 1)
    for reference_token in reference_tokens:
        current = [0]
        for index, candidate_token in enumerate(candidate_tokens, start=1):
            if reference_token == candidate_token:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current

    return round(previous[-1] / len(reference_tokens), 4)


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 4)
