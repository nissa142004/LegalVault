import math
import re
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from utils.text_extraction import get_stopwords

MAX_KEYWORDS = 10
MIN_KEYWORD_LENGTH = 3
MAX_PHRASE_WORDS = 4
LEGAL_KEYWORD_BOOSTS = {
    "agreement",
    "arbitration",
    "breach",
    "clause",
    "claim",
    "confidentiality",
    "consideration",
    "contract",
    "court",
    "damages",
    "defendant",
    "dispute",
    "indemnity",
    "injunction",
    "jurisdiction",
    "lease",
    "liability",
    "license",
    "notice",
    "obligation",
    "party",
    "payment",
    "plaintiff",
    "provision",
    "remedy",
    "rights",
    "section",
    "statute",
    "tenant",
    "term",
    "termination",
    "warranty",
}

# Frequent document furniture carries little meaning and otherwise tends to dominate
# contracts.  These supplement NLTK's general English stopword list.
RAKE_NOISE_WORDS = {
    "article", "date", "document", "hereby", "herein", "hereof", "hereto",
    "including", "page", "paragraph", "party", "parties", "remains", "said",
    "section", "shall", "thereof", "thereto", "undersigned", "whereas", "within",
}


def extract_keywords(text: str, max_keywords: int = MAX_KEYWORDS) -> list[str]:
    """Return a score-ranked, de-duplicated list of short legal key phrases."""
    keyword_limit = max(1, min(max_keywords, MAX_KEYWORDS))
    if not text or not text.strip():
        return []

    candidates = _rake_candidates(text)
    if not candidates:
        return []

    frequency = Counter(word for phrase in candidates for word in phrase)
    degree = Counter()
    for phrase in candidates:
        for word in phrase:
            degree[word] += len(phrase) - 1

    word_scores = {
        word: (degree[word] + count) / count for word, count in frequency.items()
    }
    phrase_frequency = Counter(candidates)
    phrase_scores = {}
    for phrase, occurrences in phrase_frequency.items():
        legal_hits = sum(word in LEGAL_KEYWORD_BOOSTS for word in phrase)
        # RAKE score plus modest legal-domain and repeated-phrase boosts. The
        # logarithm prevents boilerplate repetition from overwhelming relevance.
        score = sum(word_scores[word] for word in phrase)
        score *= 1 + (0.20 * legal_hits) + (0.10 * math.log1p(occurrences - 1))
        phrase_scores[phrase] = score

    ranked_phrases = sorted(
        phrase_scores,
        key=lambda phrase: (phrase_scores[phrase], phrase_frequency[phrase], len(phrase)),
        reverse=True,
    )

    keywords = []
    selected_tokens = []
    for phrase in ranked_phrases:
        normalized = " ".join(phrase)
        canonical = {_singularize(word) for word in phrase}
        if any(_is_near_duplicate(canonical, previous) for previous in selected_tokens):
            continue
        keywords.append(normalized)
        selected_tokens.append(canonical)
        if len(keywords) >= keyword_limit:
            break

    return keywords


def _rake_candidates(text: str) -> list[tuple[str, ...]]:
    """Split text on stopwords/punctuation and retain useful 1-4 word phrases."""
    stopwords = get_stopwords() | RAKE_NOISE_WORDS
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9'\-]*|[.!?;,:()\[\]{}\n]", text.lower())
    phrases = []
    current = []

    def flush():
        if not current:
            return
        # Long runs are usually headings or malformed PDF text; bounded windows
        # preserve useful phrases without emitting noisy sentence fragments.
        if len(current) <= MAX_PHRASE_WORDS:
            phrases.append(tuple(current))
        else:
            for size in range(2, MAX_PHRASE_WORDS + 1):
                phrases.extend(tuple(current[i:i + size]) for i in range(len(current) - size + 1))
        current.clear()

    for token in tokens:
        cleaned = token.strip("-'")
        if (
            not cleaned
            or not cleaned[0].isalpha()
            or cleaned in stopwords
            or len(cleaned) < MIN_KEYWORD_LENGTH
        ):
            flush()
        else:
            current.append(cleaned)
    flush()
    return phrases


def _singularize(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _is_near_duplicate(candidate: set[str], selected: set[str]) -> bool:
    if candidate == selected:
        return True
    overlap = len(candidate & selected) / max(len(candidate | selected), 1)
    return overlap >= 0.8


def summarize_textrank(text: str, max_sentences: int = 3) -> str:
    sentence_count = max(1, min(max_sentences, 20))
    try:
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.summarizers.text_rank import TextRankSummarizer

        # NLP technique: TextRank uses a graph-ranking algorithm for extractive summaries.
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = TextRankSummarizer()
        summary_sentences = summarizer(parser.document, sentence_count)
        summary = " ".join(str(sentence) for sentence in summary_sentences).strip()
        if summary:
            return summary
    except Exception:
        pass

    # Local graph-based summarizer mirrors TextRank when Sumy or NLTK data is unavailable.
    return local_textrank_summary(text, sentence_count)


def local_textrank_summary(text: str, max_sentences: int = 3) -> str:
    sentences = split_sentences(text)
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    stopword_set = get_stopwords()
    # NLP preprocessing: tokenize sentences and remove stopwords before similarity scoring.
    sentence_words = [
        [
            word
            for word in re.findall(r"[a-zA-Z][a-zA-Z0-9']*", sentence.lower())
            if word not in stopword_set
        ]
        for sentence in sentences
    ]

    scores = textrank_scores(sentence_words)
    # Keep the highest-ranked sentences but return them in their original document order.
    top_indexes = sorted(
        sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)[
            :max_sentences
        ]
    )

    return " ".join(sentences[index] for index in top_indexes)


def split_sentences(text: str) -> list[str]:
    try:
        import nltk

        # NLP technique: sentence tokenization splits the document into summary candidates.
        return [
            sentence.strip()
            for sentence in nltk.sent_tokenize(text)
            if sentence.strip()
        ]
    except Exception:
        # Regex fallback handles simple sentence boundaries without downloaded NLTK data.
        return [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text)
            if sentence.strip()
        ]


def textrank_scores(sentence_words: list[list[str]]) -> list[float]:
    sentence_count = len(sentence_words)
    scores = [1.0] * sentence_count
    # TextRank graph: each sentence is a node, and edge weights are sentence similarities.
    similarities = [
        [sentence_similarity(sentence_words[i], sentence_words[j]) for j in range(sentence_count)]
        for i in range(sentence_count)
    ]
    # PageRank-style damping controls how much rank flows through similarity edges.
    damping = 0.85

    # Iterative ranking: repeatedly update sentence scores until they stabilize enough.
    for _ in range(30):
        next_scores = []
        for i in range(sentence_count):
            rank_sum = 0.0
            for j in range(sentence_count):
                if i == j or similarities[j][i] == 0:
                    continue

                outgoing = sum(similarities[j])
                if outgoing:
                    rank_sum += (similarities[j][i] / outgoing) * scores[j]

            next_scores.append((1 - damping) + damping * rank_sum)
        scores = next_scores

    return scores


def sentence_similarity(first_words: list[str], second_words: list[str]) -> float:
    if not first_words or not second_words:
        return 0.0

    # NLP feature: word-overlap similarity estimates how related two sentences are.
    first = Counter(first_words)
    second = Counter(second_words)
    shared_words = set(first) & set(second)
    overlap = sum(first[word] + second[word] for word in shared_words)
    normalizer = math.log(len(first_words) + 1) + math.log(len(second_words) + 1)

    return overlap / normalizer if normalizer else 0.0


def rank_documents_by_tfidf(
    query: str,
    documents: list[dict],
    max_results: int = 5,
) -> list[dict]:
    searchable_documents = [
        document
        for document in documents
        if (document.get("cleaned_text") or document.get("raw_text") or "").strip()
    ]
    if not query.strip() or not searchable_documents:
        return []

    corpus = [
        document.get("cleaned_text") or document.get("raw_text", "")
        for document in searchable_documents
    ]
    vectorizer = TfidfVectorizer(stop_words="english")
    try:
        document_vectors = vectorizer.fit_transform(corpus)
    except ValueError:
        return []

    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, document_vectors).flatten()

    ranked_matches = sorted(
        (
            (document, score)
            for document, score in zip(searchable_documents, scores)
            if score > 0
        ),
        key=lambda item: item[1],
        reverse=True,
    )

    return [
        {"document": document, "score": round(float(score), 4)}
        for document, score in ranked_matches[:max_results]
    ]
