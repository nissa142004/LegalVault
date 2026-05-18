import re
import string
from pathlib import Path

import nltk
from docx import Document
from nltk.corpus import stopwords
from PyPDF2 import PdfReader

FALLBACK_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
}


def extract_text(file_path: Path) -> str:
    extension = file_path.suffix.lower()

    if extension == ".pdf":
        return extract_pdf_text(file_path)
    if extension == ".docx":
        return extract_docx_text(file_path)

    raise ValueError("Only PDF and DOCX files are supported.")


def extract_pdf_text(file_path: Path) -> str:
    reader = PdfReader(str(file_path))
    pages = [page.extract_text() or "" for page in reader.pages]

    return "\n".join(pages).strip()


def extract_docx_text(file_path: Path) -> str:
    document = Document(str(file_path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]

    return "\n".join(paragraphs).strip()


def clean_text(text: str) -> str:
    return preprocess_text(text)


def preprocess_text(text: str) -> str:
    normalized = text.lower()
    normalized = normalized.translate(str.maketrans("", "", string.punctuation))
    normalized = re.sub(r"\s+", " ", normalized).strip()

    stopword_set = get_stopwords()
    tokens = tokenize_text(normalized)
    words = [word for word in tokens if word not in stopword_set]

    return " ".join(words)


def tokenize_text(text: str) -> list[str]:
    try:
        return nltk.word_tokenize(text)
    except LookupError:
        try:
            nltk.download("punkt", quiet=True)
            return nltk.word_tokenize(text)
        except Exception:
            return re.findall(r"[a-zA-Z][a-zA-Z0-9']*", text)
    except Exception:
        return re.findall(r"[a-zA-Z][a-zA-Z0-9']*", text)


def get_stopwords() -> set[str]:
    try:
        return set(stopwords.words("english"))
    except LookupError:
        try:
            nltk.download("stopwords", quiet=True)
            return set(stopwords.words("english"))
        except Exception:
            return FALLBACK_STOPWORDS
