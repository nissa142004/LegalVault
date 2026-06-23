from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha1
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass(frozen=True)
class TfidfIndex:
    fingerprint: str
    documents: list[dict]
    vectorizer: TfidfVectorizer
    matrix: object


_INDEX_CACHE: dict[str, TfidfIndex] = {}


def _document_text(document: dict) -> str:
    return (document.get("cleaned_text") or document.get("raw_text") or "").strip()


def _document_category(document: dict) -> str:
    return (
        document.get("predicted_category")
        or document.get("category")
        or document.get("legacy_category")
        or "Uncategorized"
    )


def _fingerprint(documents: Iterable[dict]) -> str:
    digest = sha1()
    for document in documents:
        digest.update(str(document.get("_id", "")).encode("utf-8"))
        digest.update(str(document.get("updated_at") or document.get("upload_date") or "").encode("utf-8"))
        digest.update(_document_category(document).encode("utf-8"))
        digest.update(str(len(_document_text(document))).encode("utf-8"))
    return digest.hexdigest()


def build_tfidf_index(
    documents: list[dict],
    cache_key: str,
    category: str | None = None,
) -> TfidfIndex | None:
    searchable = [
        document
        for document in documents
        if _document_text(document)
        and (not category or _document_category(document) == category)
    ]
    if not searchable:
        return None

    fingerprint = _fingerprint(searchable)
    cached = _INDEX_CACHE.get(cache_key)
    if cached and cached.fingerprint == fingerprint:
        return cached

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), sublinear_tf=True)
    try:
        matrix = vectorizer.fit_transform([_document_text(document) for document in searchable])
    except ValueError:
        return None

    index = TfidfIndex(
        fingerprint=fingerprint,
        documents=searchable,
        vectorizer=vectorizer,
        matrix=matrix,
    )
    _INDEX_CACHE[cache_key] = index
    return index


def rank_documents_by_similarity(
    query: str,
    documents: list[dict],
    max_results: int = 5,
    category: str | None = None,
    cache_namespace: str = "search",
    exclude_document_id: str | None = None,
) -> list[dict]:
    if not query.strip():
        return []

    cache_key = f"{cache_namespace}:{category or 'all'}"
    index = build_tfidf_index(documents, cache_key=cache_key, category=category)
    if not index:
        return []

    query_vector = index.vectorizer.transform([query])
    scores = cosine_similarity(query_vector, index.matrix).flatten()
    ranked = sorted(
        (
            (document, float(score))
            for document, score in zip(index.documents, scores)
            if score > 0 and str(document.get("_id")) != str(exclude_document_id)
        ),
        key=lambda item: item[1],
        reverse=True,
    )

    return [
        {
            "document": document,
            "score": round(score, 4),
            "similarity_percentage": round(score * 100, 2),
        }
        for document, score in ranked[:max_results]
    ]
