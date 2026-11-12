"""
Q3 - Dictionaries: Farmer Helpline Complaint Analysis (Kisan Call Centre)
"""
import random
import string
import time
from collections import Counter

# ====================================================== the given program
calls = [
    "seeds not received seeds delayed",
    "fertiliser price high",
    "seeds price high subsidy not received",
]
STOP = {"not", "high"}


def frequencies(texts, stop):
    # TODO 1 (completed): dictionary word -> count for every word not in stop,
    # using dict.get()
    counts = {}
    for text in texts:
        for word in text.split():
            if word not in stop:
                counts[word] = counts.get(word, 0) + 1
    return counts


def top(counts, k):
    # TODO 2 (completed): k most frequent (word, count) pairs, highest count
    # first and alphabetical for ties
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:k]


print(top(frequencies(calls, STOP), 3))


# ================================================ additional implementation
def clean(text):
    """lower case, remove punctuation, split into words."""
    table = str.maketrans("", "", string.punctuation)
    return text.lower().translate(table).split()


def freq_setdefault(words, stop):
    """Same count using setdefault()."""
    counts = {}
    for w in words:
        if w not in stop:
            counts.setdefault(w, 0)
            counts[w] += 1
    return counts


def freq_get(words, stop):
    counts = {}
    for w in words:
        if w not in stop:
            counts[w] = counts.get(w, 0) + 1
    return counts


def freq_list_count(words, stop):
    """Alternative: list.count() for every distinct word: O(n * d)."""
    counts = {}
    for w in set(words):
        if w not in stop:
            counts[w] = words.count(w)
    return counts


def freq_counter(words, stop):
    return Counter(w for w in words if w not in stop)


def group_by_district(records):
    """records: (district, crop, text) -> {district: [texts]}"""
    groups = {}
    for district, crop, text in records:
        groups.setdefault(district, []).append(text)
    return groups


def group_by_crop(records):
    groups = {}
    for district, crop, text in records:
        groups.setdefault(crop, []).append(text)
    return groups


VOCAB = ("seeds fertiliser price subsidy delayed received pump water loan "
         "insurance pest rain credit market power tractor drought canal "
         "storage rate").split()
DISTRICTS = ["Thanjavur", "Madurai", "Salem", "Erode"]
CROPS = ["paddy", "cotton", "sugarcane", "turmeric"]


def make_complaints(n, seed=0):
    rnd = random.Random(seed)
    return [(rnd.choice(DISTRICTS), rnd.choice(CROPS),
             " ".join(rnd.choice(VOCAB) for _ in range(6))) for _ in range(n)]


if __name__ == "__main__":
    # ------------------------------------------------ small demonstrations
    recs = [("Salem", "cotton", "Seeds NOT received, seeds delayed!"),
            ("Erode", "turmeric", "Fertiliser price HIGH."),
            ("Salem", "paddy", "Seeds price high; subsidy not received")]
    words = [w for _, _, t in recs for w in clean(t)]
    counts = freq_get(words, STOP)
    print("\ncleaned words:", words)
    print("get()        :", counts)
    print("setdefault() :", freq_setdefault(words, STOP))
    print("top 3        :", top(counts, 3))
    print("by district  :", group_by_district(recs))
    print("by crop      :", group_by_crop(recs))
    print("empty text   :", freq_get(clean(""), STOP), top({}, 3))
    print("case/punct   :", freq_get(clean("Seeds, SEEDS; seeds!"), STOP))

    print("\nviews: ")
    d = {"seeds": 3, "price": 2}
    ks, vs, its = d.keys(), d.values(), d.items()
    d["pump"] = 1
    print("  keys()  :", ks, "| values():", vs, "| items():", its,
          "(views are LIVE - they show the later insert)")

    # -------------------------------------------------- timing experiment
    print(f"\n{'complaints':>11} {'words':>9} {'dict get s':>11} {'list.count s':>13} "
          f"{'Counter s':>10} same")
    for n in (1_000, 10_000, 100_000):
        recs = make_complaints(n, seed=n)
        words = [w for _, _, t in recs for w in clean(t)]
        t0 = time.perf_counter(); a = freq_get(words, STOP); t1 = time.perf_counter() - t0
        t0 = time.perf_counter(); b = freq_list_count(words, STOP); t2 = time.perf_counter() - t0
        t0 = time.perf_counter(); c = freq_counter(words, STOP); t3 = time.perf_counter() - t0
        print(f"{n:>11,} {len(words):>9,} {t1:>11.5f} {t2:>13.5f} {t3:>10.5f} "
              f"{a == b == dict(c)}")
    print("distinct words d =", len(set(VOCAB)))


"""
EXPECTED OUTPUT: [('seeds', 3), ('price', 2), ('received', 2)]

Why price comes before received although both occur twice: the sort key is
(-count, word). Both have count 2, so the second part of the key (the word)
breaks the tie alphabetically, and "price" < "received" (p comes before r).

DESIGN & ANALYSIS
 - How a dictionary finds a key: it computes hash(key), uses it to jump straight
   to a slot of an internal table (open addressing), and compares the key there
   (and, on a collision, follows a probe sequence). The table is resized so it
   stays sparse, therefore the average number of probes is a small constant
   -> lookup is O(1) on average and does NOT depend on how many keys are stored
   (worst case O(n) only with many collisions).
 - Dictionary vs list.count() for every distinct word: the dictionary makes ONE
   pass over n words -> O(n). list.count(w) scans the whole list for each of the
   d distinct words -> O(n * d). With d fixed this is "only" a constant factor, but
   when d grows with the data (new words appear), it becomes quadratic.
 - Order of keys in Python 3.7+: guaranteed INSERTION order (a language
   guarantee, not an accident of CPython). The dict keeps entries in a compact
   array in the order inserted; an existing key's position does not change when
   its value is updated. Sorting is still needed to rank by count.
 - Views: keys(), values(), items() return live, read-only VIEW objects of the
   dictionary: they take no copy, reflect later changes, can be iterated, and
   keys()/items() support set operations (&, |).

ENGINEERING DECISION (100,000 complaints a day): deploy the single-pass
 dictionary counting (get/setdefault) or collections.Counter. It is O(n) with
 no dependence on the number of distinct words; Counter does the same in C
 (fastest, plus most_common(k)). list.count() grows with n * d and is the slowest
 in the experiment, so it is not acceptable. If the code must have no
 imports and must stay readable for the team, use the dict-get version;
 Counter is the best practical choice.

ALTERNATIVE CONCEPT & COMPLEXITY (n words, d distinct)
 - list.count for each distinct word: time O(n * d), space O(n) for the word list
   (+ O(d) for the result).
 - dictionary / Counter: time O(n) on average, space O(d) for the table (+ the
   O(n) word list if it is built in advance; a generator can avoid that).
"""
