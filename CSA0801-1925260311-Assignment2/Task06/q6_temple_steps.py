"""
Q6 - Recursion and Its Limits (Counting Ways to Climb Temple Steps)
A devotee climbs 1 or 2 steps at a time.  ways(n) = ways(n-1) + ways(n-2),
base case: ways(0) = ways(1) = 1.
"""
import sys
import time
from functools import lru_cache

calls = 0


def ways_naive(n):
    """Ways to climb n temple steps taking 1 or 2 steps at a time."""
    global calls
    calls += 1
    if n <= 1:
        return 1
    return ways_naive(n - 1) + ways_naive(n - 2)


@lru_cache(maxsize=None)
def ways_memo(n):
    global calls
    calls += 1
    # TODO 1 (completed): same base case and recursive case as ways_naive,
    # calling ways_memo
    if n <= 1:
        return 1
    return ways_memo(n - 1) + ways_memo(n - 2)


def ways_loop(n):
    """Keeps only the last two values: O(n) time, O(1) space."""
    prev, cur = 1, 1
    for _ in range(n - 1):
        prev, cur = cur, prev + cur
    return cur if n >= 1 else 1


def count_calls(func, n):
    """Return (result, number_of_calls) for one fresh run."""
    global calls
    if hasattr(func, "cache_clear"):
        func.cache_clear()
    calls = 0
    result = func(n)
    return result, calls


def call_tree(n, depth=0, seen=None):
    """Print the call tree of the naive version (marks repeated sub-problems)."""
    if seen is None:
        seen = {}
    seen[n] = seen.get(n, 0) + 1
    print("    " * depth + f"ways({n})" + ("   <- repeated" if seen[n] > 1 else ""))
    if n <= 1:
        return 1, seen
    a, _ = call_tree(n - 1, depth + 1, seen)
    b, _ = call_tree(n - 2, depth + 1, seen)
    return a + b, seen


if __name__ == "__main__":
    # ----------- the given program --------------------------------------
    calls = 0
    print("naive:", ways_naive(25), "calls =", calls)
    calls = 0
    print("memo :", ways_memo(25), "calls =", calls)

    # ----------- correctness check n = 1..6 -----------------------------
    print("\nCorrectness check (manual value = hand calculation, program value):")
    manual = {1: 1, 2: 2, 3: 3, 4: 5, 5: 8, 6: 13}   # f(n)=f(n-1)+f(n-2)
    for n in range(1, 7):
        got = (ways_naive(n), ways_memo(n), ways_loop(n))
        print(f"  n={n}: manual={manual[n]:>2}  naive/memo/loop={got}  "
              f"{'OK' if set(got) == {manual[n]} else 'MISMATCH'}")

    # ----------- call tree n = 5 ----------------------------------------
    print("\nCall tree for n = 5 (plain recursion):")
    total, seen = call_tree(5)
    print("result:", total, "| total calls:", sum(seen.values()))
    print("sub-problem call counts:", dict(sorted(seen.items())))

    # ----------- growth investigation -----------------------------------
    print("\nPREDICTION: naive calls grow about 1.6x for every +1 in n "
          "(calls ~ 2*ways(n)-1), memo calls = n+1.")
    print(f"\n{'n':>4} | {'naive calls':>12} | {'memo calls':>10} | "
          f"{'naive time s':>12} | {'memo time s':>11}")
    for n in (10, 20, 25, 30):
        t0 = time.perf_counter(); r1, c1 = count_calls(ways_naive, n)
        t1 = time.perf_counter() - t0
        t0 = time.perf_counter(); r2, c2 = count_calls(ways_memo, n)
        t2 = time.perf_counter() - t0
        assert r1 == r2
        print(f"{n:>4} | {c1:>12,} | {c2:>10,} | {t1:>12.5f} | {t2:>11.6f}")

    # ----------- deployment: n = 1000 -----------------------------------
    print("\nDeployment decision: ways_memo(1000)")
    print("sys.getrecursionlimit() =", sys.getrecursionlimit())
    ways_memo.cache_clear()
    try:
        value = ways_memo(1000)
        print("ways_memo(1000) worked, digits:", len(str(value)))
    except RecursionError as e:
        print("RecursionError:", e)

    old = sys.getrecursionlimit()
    sys.setrecursionlimit(5000)
    ways_memo.cache_clear()
    value_memo = ways_memo(1000)
    sys.setrecursionlimit(old)
    value_loop = ways_loop(1000)
    print("raised limit to 5000 -> works:", len(str(value_memo)), "digits")
    print("loop version equals memo version:", value_loop == value_memo)

    # three approaches for n = 1000
    t0 = time.perf_counter(); ways_loop(1000); tl = time.perf_counter() - t0
    print(f"loop version time for n=1000: {tl:.6f} s, calls = 1 (no recursion)")


"""
DESIGN ANSWERS
1. Base case: n <= 1 -> 1 way (0 steps: do nothing; 1 step: one way).
   Recursive case: the last move was either 1 step (from n-1) or 2 steps
   (from n-2), so ways(n) = ways(n-1) + ways(n-2).
2. Plain recursion repeats work: ways(5) calls ways(4) and ways(3); ways(4) calls
   ways(3) again, ways(3) is computed twice, ways(2) three times, etc. (see the call
   tree above). Number of calls = 2*ways(n) - 1, which grows exponentially,
   about O(phi^n), phi = 1.618.
3. Memoisation stores each ways(k) the first time; later calls are a dictionary
   lookup, so each of the n+1 sub-problems is computed once -> O(n) time and
   O(n) cache.

CORRECTNESS (manual): ways(1)=1, ways(2)=2, ways(3)=3, ways(4)=5, ways(5)=8, ways(6)=13

PREDICTION vs RESULT: the program output matches the prediction: naive calls
= 2*ways(n) - 1 (e.g. n=25: 242,785), memo calls = n + 1 (26).

DEPLOYMENT DECISION (n up to 1,000)
 - The memoised recursion goes about 1,000 calls deep, which is at the default
   recursion limit of 1000 frames, so it fails with RecursionError: maximum
   recursion depth exceeded (the limit exists to stop runaway recursion from
   crashing the interpreter by overflowing the C stack).
 - Options: (a) raise the limit with sys.setrecursionlimit - quick, but unsafe if
   set very high (it can crash Python with a segmentation fault, and the stack
   usage O(n) remains); (b) rewrite as a loop - O(n) time, O(1) space, no
   limit at all; (c) both.
 - DECISION: use the loop (option b) in deployment. The trust only needs the
   number for n <= 1000, the loop is the simplest and fastest and cannot fail
   from depth. Keep the memoised recursion only as a teaching/test version
   to cross-check the loop (raising the limit to ~5000 for the test).

ALTERNATIVE CONCEPT: loop with the last two values
 - Plain recursion : O(phi^n) time, O(n) stack space.
 - Memoisation     : O(n) time, O(n) cache + O(n) stack space.
 - Loop            : O(n) time, O(1) auxiliary space.
 - All three were run for n = 1,000 where possible (plain recursion is impossible
   for n = 1000: ~10^208 calls).
"""
