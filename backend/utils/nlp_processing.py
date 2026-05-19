import math
import re
import string
from collections import Counter, defaultdict

from utils.text_extraction import get_stopwords


def extract_keywords(text: str, max_keywords: int = 10) -> list[str]:
    try:
        from rake_nltk import Rake

        # NLP technique: RAKE (Rapid Automatic Keyword Extraction) scores candidate phrases.
        rake = Rake(stopwords=get_stopwords(), punctuations=string.punctuation)
        rake.extract_keywords_from_text(text)
        return rake.get_ranked_phrases()[:max_keywords]
    except Exception:
        # Fallback keeps keyword extraction working when rake-nltk resources are unavailable.
        return local_rake(text, max_keywords)


def local_rake(text: str, max_keywords: int = 10) -> list[str]:
    stopword_set = get_stopwords()
    # NLP preprocessing: regex tokenization turns text into lowercase word tokens.
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9']*", text.lower())
    phrases = []
    current_phrase = []

    # RAKE candidate generation: stopwords split the text into keyword phrases.
    for word in words:
        if word in stopword_set:
            if current_phrase:
                phrases.append(current_phrase)
                current_phrase = []
        else:
            current_phrase.append(word)

    if current_phrase:
        phrases.append(current_phrase)

    # RAKE scoring: word degree and frequency estimate phrase importance.
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
