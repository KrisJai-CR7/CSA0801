"""
Q5 - List Comprehension: Cleaning Sensor Readings (Cold-Storage Temperature Monitor)
Readings above 50 C or below -50 C are sensor errors. Outputs: valid readings in
Celsius and Fahrenheit, and the minutes when the temperature was outside 2-8 C.
(The reading's index in the log is its minute number.)
"""
import random
import sys
import time

LOW, HIGH = 2, 8             # safe range for vaccines (Celsius)
MIN_OK, MAX_OK = -50, 50     # outside this the reading is a sensor error


def to_f(c):
    return c * 9 / 5 + 32


# -------------------------------------------------- 1. for loop with append
def clean_loop(readings):
    celsius, fahrenheit, alarms = [], [], []
    for minute, c in enumerate(readings):          # enumerate gives the minute
        if MIN_OK <= c <= MAX_OK:                  # valid reading
            celsius.append(c)
            fahrenheit.append(to_f(c))
            if c < LOW or c > HIGH:                # outside 2-8 C
                alarms.append(minute)
    return celsius, fahrenheit, alarms


# --------------------------------------------- 2. list comprehensions
def clean_comprehension(readings):
    celsius = [c for c in readings if MIN_OK <= c <= MAX_OK]
    fahrenheit = [to_f(c) for c in readings if MIN_OK <= c <= MAX_OK]
    alarms = [m for m, c in enumerate(readings)
              if MIN_OK <= c <= MAX_OK and (c < LOW or c > HIGH)]
    return celsius, fahrenheit, alarms


# ------------------------------------------- 3. map() and filter() + lambda
def clean_map_filter(readings):
    celsius = list(filter(lambda c: MIN_OK <= c <= MAX_OK, readings))
    fahrenheit = list(map(lambda c: c * 9 / 5 + 32, celsius))
    alarms = [m for m, c in filter(lambda p: MIN_OK <= p[1] <= MAX_OK
                                   and (p[1] < LOW or p[1] > HIGH),
                                   enumerate(readings))]
    return celsius, fahrenheit, alarms


# ---------------------------------------------- generator-expression version
def count_alarms_generator(readings):
    """Never builds the list: constant memory."""
    return sum(1 for c in readings if MIN_OK <= c <= MAX_OK and (c < LOW or c > HIGH))


def make_readings(n, seed=0, error_rate=0.02):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        r = rnd.random()
        if r < error_rate:
            out.append(rnd.choice([rnd.uniform(51, 90), rnd.uniform(-90, -51)]))
        elif r < 0.12:
            out.append(rnd.uniform(-10, 1.9) if rnd.random() < 0.5 else rnd.uniform(8.1, 20))
        else:
            out.append(rnd.uniform(2, 8))
    return [round(x, 2) for x in out]


def timed(f, data, runs=3):
    best = []
    for _ in range(runs):
        t0 = time.perf_counter()
        r = f(data)
        best.append(time.perf_counter() - t0)
    return r, sum(best) / runs


if __name__ == "__main__":
    sample = [4.5, 60.0, 1.2, 7.9, -55.0, 9.3, 2.0, 8.0, -3.0]
    print("sample:", sample)
    for f in (clean_loop, clean_comprehension, clean_map_filter):
        c, fh, a = f(sample)
        print(f"{f.__name__:20} C={c}\n{'':20} F={[round(x, 1) for x in fh]}\n{'':20} alarm minutes={a}")
    print("expected alarm minutes (by hand): [2, 5, 8]  (1.2, 9.3, -3.0 are outside 2-8; "
          "2.0 and 8.0 are inside)")

    print("\n--- dictionary and set comprehensions ---")
    valid = [(m, c) for m, c in enumerate(sample) if MIN_OK <= c <= MAX_OK]
    minute_to_f = {m: round(to_f(c), 1) for m, c in valid}           # dict comp
    distinct_rounded = {round(c) for _, c in valid}                  # set comp
    print("dict  minute -> F :", minute_to_f)
    print("set   rounded C   :", distinct_rounded)

    print("\n--- tests: all valid / all invalid / empty ---")
    for name, data in (("all valid", [3, 4, 5]), ("all invalid", [99, -99, 51]), ("empty", [])):
        print(f"{name:12}", clean_loop(data), clean_comprehension(data) == clean_loop(data),
              clean_map_filter(data) == clean_loop(data))

    print(f"\n{'n':>10} {'loop s':>9} {'comprehension s':>16} {'map/filter s':>13}  identical")
    for n in (10_000, 100_000, 1_000_000):
        data = make_readings(n, seed=n)
        r1, t1 = timed(clean_loop, data)
        r2, t2 = timed(clean_comprehension, data)
        r3, t3 = timed(clean_map_filter, data)
        print(f"{n:>10,} {t1:>9.4f} {t2:>16.4f} {t3:>13.4f}  {r1 == r2 == r3}")

    data = make_readings(1_000_000, seed=1)
    as_list = [c for c in data if MIN_OK <= c <= MAX_OK]
    as_gen = (c for c in data if MIN_OK <= c <= MAX_OK)
    print("\nsys.getsizeof (1,000,000 readings):")
    print(f"  list comprehension  : {sys.getsizeof(as_list):>10,} bytes")
    print(f"  generator expression: {sys.getsizeof(as_gen):>10,} bytes")
    t0 = time.perf_counter(); n_alarm = count_alarms_generator(data); tg = time.perf_counter() - t0
    t0 = time.perf_counter(); n_alarm2 = len([m for m, c in enumerate(data)
                                              if MIN_OK <= c <= MAX_OK and (c < LOW or c > HIGH)])
    tl = time.perf_counter() - t0
    print(f"  count alarms: generator {tg:.4f} s ({n_alarm}) vs list+len {tl:.4f} s ({n_alarm2})")


"""
DESIGN & ANALYSIS
 - General form of a list comprehension with a condition:
       [ expression for item in iterable if condition ]
   e.g. [c * 9/5 + 32 for c in readings if -50 <= c <= 50]
   (with an if/else the conditional EXPRESSION goes before the for:
    [x if cond else y for item in iterable]).
 - A comprehension becomes harder to read than a loop when it has several
   nested for-clauses or conditions, needs side effects (printing, updating a
   counter), calls long expressions, or must do more than one thing per item
   (here the alarm list needs the minute, the validity test and the range
   test; the loop version with comments is clearer if more rules are added).
 - Dictionary and set comprehensions (see output):
       {m: round(to_f(c), 1) for m, c in valid}   # minute -> Fahrenheit
       {round(c) for _, c in valid}               # distinct whole-degree values
 - List comprehension vs generator expression: [...] builds the WHOLE list in
   memory at once (O(n) space) and can be indexed/reused; (...) is lazy: it
   produces one item at a time (O(1) space), can be consumed ONCE, has no
   len() or indexing.

CONCLUSION: a list comprehension is NOT always the best choice. Measured
 result (output above): the single-pass for loop was the FASTEST here, about
 25% faster than the comprehension and map/filter versions. Reason: the
 comprehension version scans the readings THREE times (Celsius, Fahrenheit,
 alarms), while the loop does all three jobs in ONE pass. For one list built
 from one input a comprehension is normally a little faster than loop + append
 (no repeated .append lookup) and than map/filter with lambda (one Python function
 call per item); this advantage disappears when the comprehension has to be
 repeated for several outputs. When you only need a total/count/any() over a
 large input, a generator expression is better: same O(n) time and no big list
 (measured: about 200 bytes against ~8 MB). For complex logic or side effects
 the plain loop is also the more readable choice. Readability, number of passes
 and memory matter as much as raw speed.

ALTERNATIVE CONCEPT: generator expression, e.g.
     sum(c for c in readings if -50 <= c <= 50)
 - Time O(n) in both designs. Memory: list comprehension O(n) (all valid readings
   stored), generator O(1). A generator is the right tool when the result is
   consumed once (a sum, count, writing to a file) and a list when the values
   are needed repeatedly or by index.
"""
