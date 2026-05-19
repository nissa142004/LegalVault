import math
import re
import string
from collections import Counter, defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from utils.text_extraction import get_stopwords

LEGAL_TERMS = {
    "act",
    "agreement",
    "appeal",
    "arbitration",
    "assignment",
    "attorney",
    "breach",
    "case",
    "charge",
    "clause",
    "claim",
    "claims",
    "compliance",
    "confidentiality",
    "consideration",
    "contract",
    "contracts",
    "court",
    "covenant",
    "damages",
    "deed",
    "defendant",
    "defendants",
    "dispute",
    "effective",
    "enforcement",
    "evidence",
    "filing",
    "hearing",
    "indemnity",
    "injunction",
    "judgment",
    "jurisdiction",
    "law",
    "lease",
    "legal",
    "liability",
    "license",
    "litigation",
    "mortgage",
    "notice",
    "obligation",
    "obligations",
    "ordinance",
    "party",
    "parties",
    "penalty",
    "petition",
    "plaintiff",
    "plaintiffs",
    "policy",
    "precedent",
    "provision",
    "rent",
    "regulation",
    "regulations",
    "remedy",
    "renewal",
    "representation",
    "section",
    "settlement",
    "statute",
    "tenant",
    "termination",
    "terms",
    "tribunal",
    "violation",
    "warranty",
}

GENERIC_LEGAL_NOISE = {
    "document",
    "file",
    "important",
    "legal",
    "page",
    "said",
    "shall",
    "subject",
    "thereof",
    "whereas",
}


def extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
    try:
        from rake_nltk import Rake

        rake = Rake(stopwords=get_stopwords(), punctuations=string.punctuation)
        rake.extract_keywords_from_text(text)
        candidates = rake.get_ranked_phrases()[: max_keywords * 4]
    except Exception:
        candidates = local_rake(text, max_keywords * 4)

    return rank_legal_keywords(candidates, text, max_keywords)


def rank_legal_keywords(
    candidates: list[str],
    text: str,
    max_keywords: int = 10,
) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9']*", text.lower())
    frequency = Counter(words)
    ranked_keywords = []
    seen = set()

    for candidate in candidates:
        normalized = " ".join(candidate.lower().split())
        if not normalized or normalized in seen:
            continue

        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9']*", normalized)
        if not tokens or len(tokens) > 6:
            continue

        legal_hits = sum(1 for token in tokens if legal_term_match(token))
        meaningful_tokens = [
            token
            for token in tokens
            if token not in GENERIC_LEGAL_NOISE and len(token) > 2
        ]
        if not meaningful_tokens:
            continue

        if legal_hits == 0 and len(meaningful_tokens) == 1:
            continue

        frequency_score = sum(frequency[token] for token in tokens) / len(tokens)
        phrase_length_bonus = min(len(tokens), 4) * 0.25
        legal_bonus = legal_hits * 4
        score = frequency_score + phrase_length_bonus + legal_bonus

        ranked_keywords.append((candidate, score, legal_hits))
        seen.add(normalized)

    legal_keywords = [item for item in ranked_keywords if item[2] > 0]
    source = legal_keywords or ranked_keywords
    source.sort(key=lambda item: item[1], reverse=True)

    return [keyword for keyword, _, _ in source[:max_keywords]]


def legal_term_match(token: str) -> bool:
    if token in LEGAL_TERMS:
        return True

    if token.endswith("ies") and f"{token[:-3]}y" in LEGAL_TERMS:
        return True

    if token.endswith("s") and token[:-1] in LEGAL_TERMS:
        return True

    return False


def local_rake(text: str, max_keywords: int = 10) -> list[str]:
    stopword_set = get_stopwords()
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9']*", text.lower())
    phrases = []
    current_phrase = []

    for word in words:
        if word in stopword_set:
            if current_phrase:
                phrases.append(current_phrase)
                current_phrase = []
        else:
            current_phrase.append(word)

    if current_phrase:
        phrases.append(current_phrase)

    frequency = Counter(word for phrase in phrases for word in phrase)
    degree = Counter()
    for phrase in phrases:
        phrase_degree = max(len(phrase) - 1, 0)
        for word in phrase:
            degree[word] += phrase_degree

    word_scores = {
        word: (degree[word] + frequency[word]) / frequency[word]
        for word in frequency
    }

    phrase_scores = defaultdict(float)
    for phrase in phrases:
        phrase_text = " ".join(phrase)
        phrase_scores[phrase_text] += sum(word_scores[word] for word in phrase)

    ranked_phrases = sorted(
        phrase_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return [phrase for phrase, score in ranked_phrases[:max_keywords]]


def summarize_textrank(text: str, max_sentences: int = 3) -> str:
    sentence_count = max(1, min(max_sentences, 20))
    try:
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.parsers.plaintext import PlaintextParser
        from sumy.summarizers.text_rank import TextRankSummarizer

        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = TextRankSummarizer()
        summary_sentences = summarizer(parser.document, sentence_count)
        summary = " ".join(str(sentence) for sentence in summary_sentences).strip()
        if summary:
            return summary
    except Exception:
        pass

    return local_textrank_summary(text, sentence_count)


def local_textrank_summary(text: str, max_sentences: int = 3) -> str:
    sentences = split_sentences(text)
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    stopword_set = get_stopwords()
    sentence_words = [
        [
            word
            for word in re.findall(r"[a-zA-Z][a-zA-Z0-9']*", sentence.lower())
            if word not in stopword_set
        ]
        for sentence in sentences
    ]

    scores = textrank_scores(sentence_words)
    top_indexes = sorted(
        sorted(range(len(scores)), key=lambda index: scores[index], reverse=True)[
            :max_sentences
        ]
    )

    return " ".join(sentences[index] for index in top_indexes)


def split_sentences(text: str) -> list[str]:
    try:
        import nltk

        return [
            sentence.strip()
            for sentence in nltk.sent_tokenize(text)
            if sentence.strip()
        ]
    except Exception:
        return [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text)
            if sentence.strip()
        ]


def textrank_scores(sentence_words: list[list[str]]) -> list[float]:
    sentence_count = len(sentence_words)
    scores = [1.0] * sentence_count
    similarities = [
        [sentence_similarity(sentence_words[i], sentence_words[j]) for j in range(sentence_count)]
        for i in range(sentence_count)
    ]
    damping = 0.85

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
