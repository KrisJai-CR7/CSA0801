"""
Task B4 - Final Engineering Decision (5 marks)
 The board will add 100 more stations reporting every 15 minutes and receives 50,000 complaints a month.
  B4.1 sentiment scorer + summariser on >= 50 complaints, agreement with my own reading
  B4.2 index on (station, day): effect on the slowest query
  B4.3 production decision justified by measurements
plus the given "Complete the Code" program (lexicon sentiment scorer).
"""
import math
import os
import random
import sys
import tempfile
import time
import tracemalloc
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import ai_app, aqlib

# ====================================================== the given program (completed)
POSITIVE = {"good", "clean", "fast", "helpful", "improved"}
NEGATIVE = {"bad", "dirty", "slow", "rude", "smoke", "broken"}
NEGATORS = {"not", "never", "no"}


def score(text):
    """+1 per positive word, -1 per negative word; a preceding negator flips it."""
    words = text.lower().replace(".", " ").replace(",", " ").split()
    total = 0
    # TODO 1 (completed): for each word find its value (+1, -1 or 0); if the previous word is a
    # negator, flip the sign; add it to total
    for i, w in enumerate(words):
        value = 1 if w in POSITIVE else -1 if w in NEGATIVE else 0
        if value and i > 0 and words[i - 1] in NEGATORS:
            value = -value
        total += value
    return total


def label(text):
    s = score(text)
    return "positive" if s > 0 else "negative" if s < 0 else "neutral"


for c in ["Roads are clean and the bus was fast.",
          "Smoke from the factory, air is bad.",
          "The staff were not helpful.",
          "Not bad, service improved."]:
    print(f"{label(c):8} | {c}")
# Expected output:
# positive | Roads are clean and the bus was fast.
# negative | Smoke from the factory, air is bad.
# negative | The staff were not helpful.
# positive | Not bad, service improved.
# A complaint the scorer labels WRONGLY, and why:
print("\nwrongly labelled:", repr("The helpline was so helpful, I waited two hours."), "->",
      label("The helpline was so helpful, I waited two hours."), "(a human reads: negative)")
print("  Why: the scorer counts words. 'helpful' is +1 and nothing in the lexicon marks 'I waited two hours'"
      " as bad, so the sarcasm is invisible.")

# ================================================= B4.1 - 56 complaints, my own reading
COMPLAINTS = [
    ("The air near Guindy is very bad in the evening.", "negative"),
    ("Smoke from the factory fills our street every night.", "negative"),
    ("Garbage is not collected and the drains are dirty.", "negative"),
    ("The monitoring app is slow and often broken.", "negative"),
    ("The staff were rude when I reported the smell.", "negative"),
    ("Nobody answered my call about the dust problem.", "negative"),
    ("We cannot breathe, the smell from the dump is terrible.", "negative"),
    ("Burning of waste continues near the school.", "negative"),
    ("The complaint portal is broken again.", "negative"),
    ("Bad air every morning, children are coughing.", "negative"),
    ("Response to my earlier complaint was very slow.", "negative"),
    ("The dust from construction is unbearable.", "negative"),
    ("No action was taken, the factory still releases smoke.", "negative"),
    ("Water supply is not good and the road is dirty.", "negative"),
    ("The officer was never helpful.", "negative"),
    ("The traffic smoke makes my eyes burn.", "negative"),
    ("Pollution is getting worse every year.", "negative"),
    ("The helpline kept me waiting, so slow.", "negative"),
    ("Dirty roads and broken streetlights in our ward.", "negative"),
    ("I am angry that nothing was done.", "negative"),
    ("Great, another day of smoke.", "negative"),
    ("Oh wonderful, the app is broken again.", "negative"),
    ("So helpful, they closed the office at noon.", "negative"),
    ("Not helpful at all, the staff did not even listen.", "negative"),
    ("The new air purifier is not working.", "negative"),
    ("Roads are clean and the bus was fast.", "positive"),
    ("The helpline staff were helpful and polite.", "positive"),
    ("Service has improved a lot after the new station opened.", "positive"),
    ("The new sensor in Adyar works well.", "positive"),
    ("Not bad, the air was better this week.", "positive"),
    ("Thank you, the problem was solved quickly.", "positive"),
    ("The clean park near the station is a good change.", "positive"),
    ("Buses are fast and the staff are helpful.", "positive"),
    ("Air quality improved after the road was repaired.", "positive"),
    ("The complaint was resolved within a day.", "positive"),
    ("I am happy with the new air-quality display.", "positive"),
    ("The officer was never rude, very helpful.", "positive"),
    ("No smoke today, the air feels clean.", "positive"),
    ("The app is fast and easy to use.", "positive"),
    ("Good work by the pollution control team.", "positive"),
    ("The drains were cleaned and the smell is gone.", "positive"),
    ("The service is not slow.", "positive"),
    ("Pollution levels are good today.", "positive"),
    ("What is the PM2.5 in Adyar today?", "neutral"),
    ("Please tell me the office timing of the board.", "neutral"),
    ("I want to know how to register a complaint.", "neutral"),
    ("The board meeting is on Monday.", "neutral"),
    ("Where can I see the daily report?", "neutral"),
    ("Is the data updated every hour?", "neutral"),
    ("Kindly share the contact number of the Guindy station.", "neutral"),
    ("Clean air in the morning, bad air at night.", "neutral"),
    ("The roads are clean but the bus is slow and rude.", "negative"),
    ("Staff were helpful, but the app is slow and the data is bad.", "negative"),
    ("The new buses are fast, however the smoke from old ones is still there.", "negative"),
    ("Good display, but it is broken in the evening.", "negative"),
    ("The air is not good, but the response was fast.", "negative"),
]


def agreement(fn, items):
    right = sum(fn(t) == y for t, y in items)
    return right, len(items)


# ---- summariser test set: intro + key sentence + closing, key position varies
KEYS = [  # (key sentence, has repeated important words?)
    ("Factory smoke fills our street and the smoke irritates the children's eyes.", True),
    ("The garbage near the market is never cleared and the garbage smells terrible.", True),
    ("Construction dust covers every house, and the dust enters the kitchen.", True),
    ("The streetlights in our lane stay broken for weeks, the broken lights cause accidents.", True),
    ("The drain overflow in Velachery floods the road when it rains, the overflow is dangerous.", True),
    ("The dump behind our house smells terrible.", False),
    ("Buses on route 21 skip our stop.", False),
    ("The sensor at the school shows wrong values.", False),
    ("Open burning happens near the lake every evening.", False),
    ("Noise from the plant continues after midnight.", False),
]
INTROS = ["Good morning, I am writing to the pollution control board.",
          "I live in ward 12 near the main road.",
          "This is my complaint for this week.",
          "I have complained about this complaint many times, but no complaint was ever answered."]
CLOSINGS = ["Please take action soon.", "Kindly respond to this complaint.", "Thank you for your time.",
            "I will wait for your reply."]


def make_summary_set(n=50, seed=4):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        key, _rep = rnd.choice(KEYS)
        parts = [rnd.choice(INTROS), rnd.choice(CLOSINGS)]
        pos = rnd.randrange(3)
        parts.insert(pos, key)
        out.append((" ".join(parts), key))
    return out


# ---- a small trained model for comparison: multinomial Naive Bayes
class NaiveBayes:
    def __init__(self):
        self.class_count, self.word_count, self.vocab = Counter(), defaultdict(Counter), set()

    def fit(self, items):
        for text, y in items:
            self.class_count[y] += 1
            for w in ai_app.words_of(text):
                self.word_count[y][w] += 1
                self.vocab.add(w)
        return self

    def predict(self, text):
        total = sum(self.class_count.values())
        best, best_lp = None, -1e18
        for y, cnt in self.class_count.items():
            lp = math.log(cnt / total)
            denom = sum(self.word_count[y].values()) + len(self.vocab) + 1
            for w in ai_app.words_of(text):
                lp += math.log((self.word_count[y][w] + 1) / denom)
            if lp > best_lp:
                best, best_lp = y, lp
        return best


def b41():
    print("\nB4.1 SENTIMENT SCORER ON 56 COMPLAINTS (labels = my own reading)")
    right, n = agreement(label, COMPLAINTS)
    print(f"  agreement with my labels: {right} of {n} = {100 * right / n:.0f}%")
    conf = Counter((y, label(t)) for t, y in COMPLAINTS)
    print("  confusion (my label -> scorer):",
          {f"{a}->{b}": c for (a, b), c in sorted(conf.items())})
    wrong = [(t, y, label(t)) for t, y in COMPLAINTS if label(t) != y]
    print(f"  {len(wrong)} disagreements, 6 examples:")
    for t, y, g in wrong[:6]:
        print(f"    me={y:<8} scorer={g:<8} {t}")
    kinds = Counter()
    for t, y, g in wrong:
        kinds["scorer says neutral (words not in the lexicon)" if g == "neutral" else
              "scorer picks the wrong side (sarcasm / mixed / negation)"] += 1
    print("  reasons:", dict(kinds))

    print("\n  SUMMARISER (1 sentence) on 50 multi-sentence complaints (key sentence known by construction)")
    data = make_summary_set()
    ext = sum(ai_app.summarise(t, 1) == [k] for t, k in data)
    first = sum(ai_app.summarise_first_k(t, 1) == [k] for t, k in data)
    print(f"    key sentence chosen: frequent-words summariser {ext}/50 | first sentence {first}/50")
    t, k = next((t, k) for t, k in data if ai_app.summarise(t, 1) != [k])
    print("    a failure of the frequent-words summariser:\n      text   :", t,
          "\n      chosen :", ai_app.summarise(t, 1)[0], "\n      wanted :", k)
    return right / n, ext / 50, first / 50


# ======================================================================= B4.2 index
def build_big_db(path, stations=120, days=365):
    rows = aqlib.generate_rows(stations, days, seed=2, dirty=False)
    clean = [(r[0], r[1], int(r[2]), float(r[3]), float(r[4]), float(r[5]), float(r[6])) for r in rows]
    return aqlib.build_db(clean, str(path)), len(clean)


def avg_query(con, name):
    return con.execute("SELECT AVG(r.pm25) FROM readings r JOIN stations s USING(station_id) "
                       "WHERE s.name = ? AND r.day BETWEEN '2026-10-01' AND '2026-10-31'", (name,)).fetchone()[0]


def timed(fn, *args, reps=20):
    t0 = time.perf_counter()
    for _ in range(reps):
        fn(*args)
    return (time.perf_counter() - t0) / reps


def plan(con, sql, args):
    return " | ".join(r[3] for r in con.execute("EXPLAIN QUERY PLAN " + sql, args))


def b42(tmpdir):
    print("\nB4.2 INDEX ON (station_id, day)   (120 stations x 365 days x 24 h)")
    path = Path(tmpdir) / "big.db"
    t0 = time.perf_counter(); con, n = build_big_db(path); t_build = time.perf_counter() - t0
    size0 = os.path.getsize(path) / 1e6
    print(f"  database: {n:,} rows built in {t_build:.1f} s, file {size0:.1f} MB")
    q_station = ("SELECT AVG(r.pm25) FROM readings r WHERE r.station_id = ? AND r.day BETWEEN "
                 "'2026-10-01' AND '2026-10-31'")
    queries = {
        "Q1 one station, one month (avg)": lambda: avg_query(con, "Adyar"),
        "Q2 one station, daily means": lambda: con.execute(
            "SELECT day, AVG(pm25) FROM readings WHERE station_id = 5 GROUP BY day").fetchall(),
        "Q3 city-wide mean by hour": lambda: con.execute(
            "SELECT hour, AVG(pm25) FROM readings GROUP BY hour").fetchall(),
    }
    before = {name: timed(f, reps=5 if name.startswith("Q3") else 10) for name, f in queries.items()}
    print("  plan before:", plan(con, q_station, (5,)))
    t0 = time.perf_counter()
    con.execute("CREATE INDEX idx_station_day ON readings(station_id, day)"); con.commit()
    t_idx = time.perf_counter() - t0
    size1 = os.path.getsize(path) / 1e6
    after = {name: timed(f, reps=5 if name.startswith("Q3") else 10) for name, f in queries.items()}
    print("  plan after :", plan(con, q_station, (5,)))
    print(f"\n  {'query':<36}{'before ms':>11}{'after ms':>10}{'speed-up':>10}")
    for name in queries:
        print(f"  {name:<36}{before[name] * 1000:>11.2f}{after[name] * 1000:>10.2f}{before[name] / after[name]:>9.1f}x")
    print(f"  index cost: build {t_idx:.2f} s, file grows {size0:.1f} -> {size1:.1f} MB (+{100 * (size1 - size0) / size0:.0f}%)")
    # insertion cost of the index for one day of new data (one station-day batch)
    batch = [(5, "2026-12-31", h, 50.0, 80.0, 30.0, 27.0) for h in range(24)] * 100
    c2 = aqlib.build_db([], str(Path(tmpdir) / "e1.db")); c3 = aqlib.build_db([], str(Path(tmpdir) / "e2.db"))
    c3.execute("CREATE INDEX i ON readings(station_id, day)")
    ins = "INSERT INTO readings(station_id, day, hour, pm25, pm10, no2, temp_c) VALUES (?,?,?,?,?,?,?)"
    t0 = time.perf_counter(); c2.executemany(ins, batch); c2.commit(); a = time.perf_counter() - t0
    t0 = time.perf_counter(); c3.executemany(ins, batch); c3.commit(); b = time.perf_counter() - t0
    print(f"  inserting {len(batch):,} rows: without index {a * 1000:.1f} ms | with index {b * 1000:.1f} ms")
    con.close()
    return n, size1 / n * 1e6, before, after


# ======================================================================= B4.3 scale
def b43(n_rows, bytes_per_row, agree_lex):
    print("\nB4.3 PRODUCTION DECISION - measurements at the new scale")
    stations, per_day = 112, 112 * 96
    year = per_day * 365
    print(f"  readings: {stations} stations x 96 per day = {per_day:,}/day = {year:,}/year "
          f"({year / n_rows:.1f}x the 1.05 million-row test)")
    print(f"  storage (SQLite incl. index, measured {bytes_per_row:.0f} bytes/row): {year * bytes_per_row / 1e6:,.0f} MB per year")
    raw = aqlib.generate_rows(12, 30, seed=9)
    t0 = time.perf_counter(); clean, rep = aqlib.clean_rows(raw); dt = time.perf_counter() - t0
    rate = len(raw) / dt
    print(f"  cleaning speed (plain Python): {rate:,.0f} rows/s -> one day ({per_day:,} rows) in "
          f"{per_day / rate:.2f} s; a whole year in {year / rate / 60:.1f} min if ever re-cleaned")

    rnd = random.Random(1)
    texts = [" ".join(rnd.choice(COMPLAINTS)[0] for _ in range(rnd.randint(1, 3))) for _ in range(50_000)]
    t0 = time.perf_counter(); labels = [label(t) for t in texts]; t_lab = time.perf_counter() - t0
    t0 = time.perf_counter(); [ai_app.summarise(t, 1) for t in texts]; t_sum = time.perf_counter() - t0
    print(f"  50,000 complaints (a month): sentiment {t_lab:.2f} s, summaries {t_sum:.2f} s "
          f"({t_lab / 50_000 * 1e6:.0f} and {t_sum / 50_000 * 1e6:.0f} microseconds each)")
    print("  label mix of the month:", {k: f"{100 * v / 50_000:.0f}%" for k, v in Counter(labels).most_common()})

    # trained model, leave-one-out on the 56 labelled complaints
    t0 = time.perf_counter()
    hits = 0
    for i, (t, y) in enumerate(COMPLAINTS):
        nb = NaiveBayes().fit(COMPLAINTS[:i] + COMPLAINTS[i + 1:])
        hits += nb.predict(t) == y
    t_loo = time.perf_counter() - t0
    tracemalloc.start()
    nb = NaiveBayes().fit(COMPLAINTS)
    mem = tracemalloc.get_traced_memory()[1] / 1024
    tracemalloc.stop()
    t0 = time.perf_counter()
    for t in texts[:5000]:
        nb.predict(t)
    t_nb = (time.perf_counter() - t0) / 5000
    print(f"\n  lexicon scorer     : agreement {100 * agree_lex:.0f}% (56 complaints), {t_lab / 50_000 * 1e6:.0f} us/complaint, "
          f"memory ~ 0 (a 14-word list)")
    print(f"  Naive Bayes (LOO)  : agreement {100 * hits / 56:.0f}% (leave-one-out on the same 56), "
          f"{t_nb * 1e6:.0f} us/complaint, model {mem:.0f} KB for {len(nb.vocab)} words")
    return agree_lex, hits / 56


if __name__ == "__main__":
    a_lex, a_sum, a_first = b41()
    tmp = tempfile.mkdtemp()
    n_rows, bpr, before, after = b42(tmp)
    lex, nb = b43(n_rows, bpr, a_lex)


"""
B4.3 - DECISION (justified by the measurements above)
 STORAGE. Keep SQLite for the pilot and the daily report (one writer, a single file, 3.9 million rows a
   year is only a few hundred MB), with an INDEX on (station_id, day): it turns a station/month query
   from a full scan of the table into an index search (speed-up in the B4.2 table) at the price of a
   larger file and slower inserts. City-wide aggregates (Q3) scan everything whatever the index, so they
   should be pre-computed once per day into a summary table. If many people must write at the same time, or the data
   grows to tens of millions of rows, move to a client-server database (PostgreSQL) with the same SQL and schema.
 CLEANING. Clean INCREMENTALLY: each day's files are cleaned when they arrive (about 10,000 rows take
   a fraction of a second with the plain-Python rules) and only clean rows are stored with executemany and one
   commit per batch. Keep the raw files; never re-clean a year at a time. Rejected rows and counts go to a log.
 ANALYSIS. Daily and monthly reports use SQL GROUP BY on the indexed table (B3: the query is fast once
   the data are loaded); pandas is for ad-hoc exploration and charts.
 SENTIMENT AND SUMMARIES. Speed is no problem: the lexicon scorer needs 2 microseconds a complaint (0.11 s for the
   50,000 of a month) and the summariser 13 microseconds (0.63 s). ACCURACY is the problem: the lexicon
   agreed with my reading in 40 of 56 complaints (71%); 15 of its 16 mistakes were 'neutral' because the
   words (dust, terrible, worse, thank, resolved ...) are not in the 14-word list, and it also fails on
   sarcasm, mixed opinions and double negatives (B2). So the simple scorer is good enough for ONE purpose -
   watching the overall trend of positive/negative counts and finding frequent words - and NOT good
   enough to judge an individual complaint or to decide what a citizen is told.
   A TRAINED MODEL was tried as a comparison: Naive Bayes trained on the same 56 complaints (leave-one-out) agreed
   in only 41% of cases, WORSE than the lexicon, because 56 examples are far too few to learn from
   (190 distinct words). It needs about 18 microseconds per complaint and 28 KB of memory, so cost is not the
   obstacle either: labelled DATA is. DECISION: deploy the lexicon scorer now, extend its word list using the
   disagreements and send 'neutral' / mixed results to a human reviewer; label a sample of the monthly
   complaints (a few thousand), train a classifier on them and switch only when it beats the lexicon on a
   held-out set of labelled complaints.
   SUMMARISER: the frequent-words method chose the key sentence in 34 of 50 test complaints (68%) against
   18 of 50 (36%) for 'first sentence'; it fails when a filler sentence repeats a word (as 'complaint' in
   the failure shown). The test set was constructed, so real complaints will be harder: use it as a
   'top sentence and keywords' aid for a human reader, not as an automatic summary.
"""
