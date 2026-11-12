"""
Q1 - Lists and Slicing: Daily Rainfall Records (Village Rain-Gauge Station)
"""
import random
import time
from collections import deque


# ----------------------------------------------------------- implementation
def weekly_totals(readings):
    """Weekly totals with slicing. The last (short) week is included."""
    return [sum(readings[i:i + 7]) for i in range(0, len(readings), 7)]


def max_min_with_positions(values):
    """Return (max, index_of_max, min, index_of_min); first occurrence wins."""
    if not values:
        return None
    hi, lo = max(values), min(values)
    return hi, values.index(hi), lo, values.index(lo)


def moving_average_naive(readings, w=7):
    """Re-add the 7 values of every window: about 6 additions per window."""
    if len(readings) < w:
        return []
    out = []
    for i in range(len(readings) - w + 1):
        total = 0
        for v in readings[i:i + w]:
            total += v
        out.append(total / w)
    return out


def moving_average_running(readings, w=7):
    """Running sum: add the entering value, subtract the leaving value."""
    if len(readings) < w:
        return []
    total = sum(readings[:w])
    out = [total / w]
    for i in range(w, len(readings)):
        total += readings[i] - readings[i - w]
        out.append(total / w)
    return out


def dry_days(readings):
    """Day numbers (1-based) with 0 mm."""
    return [day for day, mm in enumerate(readings, start=1) if mm == 0]


# --------------------------------------------------- alternative concepts
def moving_average_deque(readings, w=7):
    window = deque(maxlen=w)           # oldest value drops out automatically
    total, out = 0, []
    for v in readings:
        if len(window) == w:
            total -= window[0]
        window.append(v)
        total += v
        if len(window) == w:
            out.append(total / w)
    return out


def make_readings(n, seed=1):
    rnd = random.Random(seed)
    return [0 if rnd.random() < 0.55 else round(rnd.uniform(0.5, 60), 1)
            for _ in range(n)]


def timed(f, *a):
    t0 = time.perf_counter()
    r = f(*a)
    return r, time.perf_counter() - t0


if __name__ == "__main__":
    readings = make_readings(365)
    print("365 readings, first 14:", readings[:14])

    wt = weekly_totals(readings)
    print(f"\nweekly totals: {len(wt)} weeks (52 full + 1 day), first 5:",
          [round(x, 1) for x in wt[:5]])
    full = wt[:52]
    wet, dry = max(full), min(full)
    print(f"wettest full week: week {full.index(wet) + 1} = {wet:.1f} mm")
    print(f"driest  full week: week {full.index(dry) + 1} = {dry:.1f} mm")

    hi, ihi, lo, ilo = max_min_with_positions(readings)
    print(f"max reading {hi} mm at index {ihi} (day {ihi + 1}); "
          f"min {lo} mm at index {ilo} (day {ilo + 1})")

    ma = moving_average_running(readings)
    print("7-day moving average: first 3 =", [round(x, 2) for x in ma[:3]],
          "| count =", len(ma))
    dd = dry_days(readings)
    print("dry days:", len(dd), "| first 10:", dd[:10])

    # slicing explanations demonstrated on the list
    print("\nreadings[7:14] =", readings[7:14], "(days 8-14: the 2nd week)")
    print("readings[-7:]  =", readings[-7:], "(last seven days)")
    print("readings[::7]  =", readings[::7][:6], "... (every 7th day, "
          f"{len(readings[::7])} values: days 1, 8, 15, ...)")

    # hand check on a small list
    small = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    print("\nHand check", small, "-> expected [4.0, 5.0, 6.0]:",
          moving_average_naive(small), moving_average_running(small),
          moving_average_deque(small))

    # edge cases
    print("empty list      :", moving_average_naive([]), moving_average_running([]),
          weekly_totals([]), max_min_with_positions([]), dry_days([]))
    print("3 values (<7)   :", moving_average_naive([1, 2, 3]),
          moving_average_running([1, 2, 3]), weekly_totals([1, 2, 3]))
    print("exactly 7 values:", moving_average_naive([7] * 7), moving_average_running([7] * 7))

    # ---------------------------- derived counts vs measurements
    print("\nDERIVED ADDITIONS for n readings (window w = 7, windows = n - 6):")
    print("  naive          : 6 per window -> 6(n - 6)")
    print("  running sum    : 6 for the first window + 2 per slide -> 6 + 2(n - 7)")
    print(f"\n{'n':>8} {'naive adds':>12} {'running adds':>13} {'naive s':>10} "
          f"{'running s':>10} {'deque s':>9} {'time ratio':>11} {'add ratio':>10} same")
    for n in (365, 36_500, 365_000):
        data = make_readings(n, seed=n)
        a, t1 = timed(moving_average_naive, data)
        b, t2 = timed(moving_average_running, data)
        c, t3 = timed(moving_average_deque, data)
        same = all(abs(x - y) < 1e-6 and abs(x - z) < 1e-6 for x, y, z in zip(a, b, c)) \
            and len(a) == len(b) == len(c)
        add_n, add_r = 6 * (n - 6), 6 + 2 * (n - 7)
        print(f"{n:>8} {add_n:>12,} {add_r:>13,} {t1:>10.5f} {t2:>10.5f} {t3:>9.5f} "
              f"{t1 / t2:>11.2f} {add_n / add_r:>10.2f} {same}")

    # insertion cost
    big = make_readings(365_000)
    _, t_ins = timed(lambda: [big.insert(0, 1.0) for _ in range(200)])
    _, t_app = timed(lambda: [big.append(1.0) for _ in range(200)])
    print(f"\n200 inserts at the front of 365,000: {t_ins:.5f} s | "
          f"200 appends: {t_app:.6f} s")


"""
DESIGN & ANALYSIS
Pseudocode for the moving average (running sum)
    function moving_average(readings, w = 7):
        if length(readings) < w: return empty list
        total <- sum(readings[0 .. w-1])           // w - 1 additions
        result <- [ total / w ]
        for i from w to length(readings) - 1:
            total <- total + readings[i] - readings[i - w]   // 1 add + 1 subtract
            append total / w to result
        return result

What the slices return (365 readings, index 0 = day 1)
  readings[7:14]  items at indices 7..13: days 8-14 = the SECOND week (7 items;
                  the stop index 14 is excluded).
  readings[-7:]   the LAST seven readings (days 359-365).
  readings[::7]   every 7th item starting at index 0: days 1, 8, 15, ... 365
                  (53 values). Slicing always returns a NEW list (a shallow copy).

Why a list is suitable: the data is ordered by date, has a fixed natural index,
is read many times by position and slice, and grows by appending a new
reading each day. Costs: append O(1) amortised; insert(i, x) O(n - i)
(shifts everything after i); pop() from the end O(1) but pop(0) / pop(i) O(n - i);
sort() O(n log n).

Derived additions (n readings, window 7, n - 6 windows)
  naive: each window sums 7 numbers = 6 additions -> 6(n - 6) ~ 6n
  running sum: first window 6 additions, then 1 addition and 1 subtraction per
  slide -> 6 + 2(n - 7) ~ 2n.
  Ratio -> 3: the running sum needs about one third of the additions (the
  measured addition ratio is 2.98-3.00). The measured TIME ratio (about 3.2-4.1)
  is close to this: it also includes the slice creation and inner-loop overhead of
  the naive version, so it is not exactly the same as the addition ratio.

DESIGN QUESTION (late reading): list.insert(i, x) costs O(n - i): it shifts the
  tail one place right (O(n) in the worst case: ~365,000 shifts is
  noticeable; see the timing above). For 365 readings it is negligible and a
  list is still the right choice (a late reading is rare). Keep the list when
  inserts are rare and the main work is slicing/averaging. If late arrivals are
  common, use a dict keyed by date (O(1) insert, but no slicing) or keep a
  sorted structure (bisect.insort is still O(n) for the shift).

ALTERNATIVE CONCEPT & COMPLEXITY (n days)
  naive slicing: time O(7n) = O(n) with a big constant, space O(n) output +
      O(7) for each temporary slice.
  running sum  : time O(n), space O(n) output + O(1) extra.
  deque(maxlen=7) : time O(n); the deque keeps only the last 7 values, so
      the working space is O(7) = O(1) in addition to the output. Good for a
      live stream (no need to keep the whole year in memory); but there is no
      random access or slicing of the old data.
  dictionary keyed by date: lookup by date O(1), inserting a late reading O(1);
      but a window needs 7 lookups per day (O(7n) again unless a running sum
      is used) and it uses more memory per reading than a list.
"""
