import re
import string

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

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

TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z0-9']*")
_SPACY_NLP = None
_SPACY_LOAD_ATTEMPTED = False


def preprocess_text(text: str, lemmatize: bool = True) -> str:
    tokens = tokenize_text(clean_text(text))
    stopword_set = get_stopwords()
    filtered_tokens = [
        token
        for token in tokens
        if token not in stopword_set and len(token) > 1
    ]

    if lemmatize:
        filtered_tokens = lemmatize_tokens(filtered_tokens)

    return " ".join(filtered_tokens)


def clean_text(text: str) -> str:
    normalized = text.lower()
    normalized = normalized.translate(str.maketrans("", "", string.punctuation))
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def tokenize_text(text: str) -> list[str]:
    try:
        return [
            token
            for token in nltk.tokenize.wordpunct_tokenize(text)
            if TOKEN_PATTERN.fullmatch(token)
        ]
    except Exception:
        return TOKEN_PATTERN.findall(text)


def lemmatize_tokens(tokens: list[str]) -> list[str]:
    spacy_lemmas = lemmatize_with_spacy(tokens)
    if spacy_lemmas:
        return spacy_lemmas

    return lemmatize_with_nltk(tokens)


def lemmatize_with_spacy(tokens: list[str]) -> list[str]:
    global _SPACY_LOAD_ATTEMPTED, _SPACY_NLP

    try:
        if not _SPACY_LOAD_ATTEMPTED:
            _SPACY_LOAD_ATTEMPTED = True
            import spacy

            _SPACY_NLP = spacy.load("en_core_web_sm", disable=["parser", "ner"])

        if _SPACY_NLP is None:
            return []

        doc = _SPACY_NLP(" ".join(tokens))
        return [token.lemma_ for token in doc if token.lemma_ and token.lemma_ != "-PRON-"]
    except Exception:
        return []


def lemmatize_with_nltk(tokens: list[str]) -> list[str]:
    try:
        nltk.data.find("corpora/wordnet")
        lemmatizer = WordNetLemmatizer()
        return [lemmatizer.lemmatize(token) for token in tokens]
    except Exception:
        return tokens


def get_stopwords() -> set[str]:
    try:
        nltk.data.find("corpora/stopwords")
        return set(stopwords.words("english"))
    except Exception:
        return FALLBACK_STOPWORDS
