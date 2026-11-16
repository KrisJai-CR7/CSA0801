"""
common/ai_app.py - the introductory AI application for citizen complaints (A5):
lexicon sentiment scorer with negation, extractive summariser, rule-based chatbot.
"""
import re
import sqlite3
from collections import Counter

POSITIVE = {"good", "clean", "fast", "helpful", "improved"}
NEGATIVE = {"bad", "dirty", "slow", "rude", "smoke", "broken"}
NEGATORS = {"not", "never", "no"}
STOP = {"the", "a", "an", "is", "are", "was", "were", "and", "or", "of", "to", "in", "on", "at",
        "for", "from", "it", "this", "that", "we", "i", "my", "our", "with", "by", "as", "be",
        "has", "have", "had", "very", "so", "but", "please", "kindly", "also"}


def words_of(text):
    return re.findall(r"[a-z']+", text.lower())


def score(text):
    """+1 per positive word, -1 per negative word; a preceding negator flips it."""
    words = text.lower().replace(".", " ").replace(",", " ").split()
    total = 0
    for i, w in enumerate(words):
        value = 1 if w in POSITIVE else -1 if w in NEGATIVE else 0
        if value and i > 0 and words[i - 1] in NEGATORS:
            value = -value
        total += value
    return total


def label(text):
    s = score(text)
    return "positive" if s > 0 else "negative" if s < 0 else "neutral"


# ------------------------------------------------------------ extractive summariser
def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def summarise(text, k=1):
    """Pick the k sentences whose important (non-stop) words are most frequent in the text."""
    sentences = split_sentences(text)
    if len(sentences) <= k:
        return sentences
    freq = Counter(w for w in words_of(text) if w not in STOP)
    def sentence_score(s):
        ws = [w for w in words_of(s) if w not in STOP]
        return sum(freq[w] for w in ws) / (len(ws) ** 0.5 or 1)
    ranked = sorted(range(len(sentences)), key=lambda i: (-sentence_score(sentences[i]), i))
    return [sentences[i] for i in sorted(ranked[:k])]


def summarise_first_k(text, k=1):
    return split_sentences(text)[:k]


# ------------------------------------------------------------------- rule-based chatbot
def chatbot(question, con, stations=None):
    """Keyword + database chatbot. Returns a reply string. Limitations: see Part A (A5.2)."""
    q = question.lower()
    names = stations or [r[0] for r in con.execute("SELECT name FROM stations")]
    station = next((n for n in names if n.lower() in q), None)
    metric = "pm10" if "pm10" in q else "no2" if "no2" in q else "temp_c" \
        if ("temperature" in q or "temp" in q) else "pm25"
    if any(w in q for w in ("hello", "hi ", "help")) and station is None and "pm" not in q:
        return "Hello! Ask me e.g. 'What is the PM2.5 in Adyar today?'"
    if station is None:
        return "Which station? I know: " + ", ".join(sorted(names)) + "."
    day = con.execute("SELECT MAX(day) FROM readings").fetchone()[0]      # 'today' = latest day
    if "yesterday" in q:
        day = con.execute("SELECT MAX(day) FROM readings WHERE day < ?", (day,)).fetchone()[0]
    row = con.execute(
        f"SELECT AVG({metric}) FROM readings r JOIN stations s USING(station_id) "
        "WHERE s.name = ? AND r.day = ?", (station, day)).fetchone()
    if row[0] is None:
        return f"No {metric} data for {station} on {day}."
    unit = "degC" if metric == "temp_c" else "ug/m3"
    return f"{metric.upper()} in {station} on {day}: average {row[0]:.1f} {unit}."
