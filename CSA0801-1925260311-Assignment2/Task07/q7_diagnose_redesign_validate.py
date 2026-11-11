"""
Q7 - Diagnose, Redesign and Validate (13 Marks)

Program selected: the plain recursive temple-step counter from Q6 (ways_naive).
It is correct but does not scale: at n = 30 it already needs 2.7 million calls.

Parts:  A diagnose | B objective | C redesign | D prediction | E implement + validate
        F critical evaluation (see the text at the bottom of this file)
Raw data is also written to q7_results.csv.
"""
import csv
import os
import sys
import time

# ----------------------------------------------------------- ORIGINAL PROGRAM
calls_original = 0


def ways_original(n):
    global calls_original
    calls_original += 1
    if n <= 1:
        return 1
    return ways_original(n - 1) + ways_original(n - 2)


# ------------------------------------------------------------------- REDESIGN
# Bottom-up dynamic programming that keeps ONLY the last two values.
# It exploits "optimal substructure + overlapping sub-problems" and needs no
# recursion, no cache and no recursion limit.
ops_redesign = 0


def ways_redesigned(n):
    global ops_redesign
    ops_redesign = 0
    prev, cur = 1, 1                  # ways(0), ways(1)
    for _ in range(2, n + 1):
        prev, cur = cur, prev + cur
        ops_redesign += 1             # one addition per step
    return cur


# --------------------------------------------------- A. DIAGNOSE (evidence)
def diagnose():
    """Count calls and how often each sub-problem is recomputed."""
    global calls_original
    print("A. DIAGNOSE THE BOTTLENECK")
    print(f"{'n':>4} {'calls':>12} {'distinct sub-problems':>22} {'calls / distinct':>17}")
    for n in (5, 10, 15, 20, 25):
        calls_original = 0
        ways_original(n)
        distinct = n + 1               # ways(0) .. ways(n)
        print(f"{n:>4} {calls_original:>12,} {distinct:>22} {calls_original / distinct:>17.1f}")
    print("  -> Most work is done inside the repeated calls; the count that grows"
          " with the input is the number of function calls (exponential in n)\n"
          "  -> although only n+1 different values are ever needed. Work is"
          " unnecessarily repeated.\n")


# ------------------------------------------------ E. IMPLEMENT AND VALIDATE
def validate_and_measure():
    global calls_original
    rows = []
    print("D. PREDICTION (before running)")
    print("  original calls = 2*ways(n) - 1 (exponential, ~1.6x per +1 in n);")
    print("  redesign operations = n - 1 additions (linear); redesign must give identical "
          "answers and run n = 1000 with no RecursionError.\n")

    print("E. IMPLEMENT AND VALIDATE")
    print("  Correctness: original vs redesign for n = 0..30")
    ok = True
    for n in range(0, 31):
        calls_original = 0
        if ways_original(n) != ways_redesigned(n):
            ok = False
            print("   MISMATCH at", n)
    print("  all identical for n = 0..30:", ok)

    print(f"\n  {'n':>5} | {'original calls':>14} | {'redesign ops':>12} | "
          f"{'original s':>11} | {'redesign s':>11} | predicted calls ok")
    for n in (10, 20, 25, 30, 32):
        calls_original = 0
        t0 = time.perf_counter()
        r1 = ways_original(n)
        t_old = time.perf_counter() - t0
        c_old = calls_original
        t0 = time.perf_counter()
        r2 = ways_redesigned(n)
        t_new = time.perf_counter() - t0
        pred = 2 * r1 - 1
        print(f"  {n:>5} | {c_old:>14,} | {ops_redesign:>12} | "
              f"{t_old:>11.5f} | {t_new:>11.7f} | {c_old == pred}")
        rows.append([n, c_old, ops_redesign, t_old, t_new])

    # n = 1000 and 100000 only for the redesign (original is impossible)
    for n in (1000, 10_000):
        t0 = time.perf_counter()
        value = ways_redesigned(n)
        t_new = time.perf_counter() - t0
        print(f"  {n:>5} | {'impossible':>14} | {ops_redesign:>12} | "
              f"{'-':>11} | {t_new:>11.7f} | digits = {len(str(value))}")
        rows.append([n, "n/a", ops_redesign, "n/a", t_new])
    # original on n = 1000 is hopeless: show the recursion limit message
    sys.setrecursionlimit(1000)
    try:
        ways_original(1000)
    except RecursionError as e:
        print("  original at n = 1000 -> RecursionError (and would need ~10^208 calls)")

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "q7_results.csv")
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["n", "original_calls", "redesign_operations",
                    "original_seconds", "redesign_seconds"])
        w.writerows(rows)
    print("  raw data written to", os.path.basename(path))


if __name__ == "__main__":
    diagnose()
    validate_and_measure()


"""
=============================================================================
A. DIAGNOSE THE BOTTLENECK (2 marks)
 Evidence (output above): for n = 25 the program makes 242,785 calls although
 there are only 26 different sub-problems (ways(0)..ways(25)): about 9,300
 calls per distinct sub-problem. The count that grows with the input is the
 number of recursive CALLS: it multiplies by about 1.618 for each +1 in n
 (O(phi^n)). Yes, work is unnecessarily repeated: ways(3) is recomputed
 many times inside ways(5), and the same happens at every level.

B. DESIGN OBJECTIVE (2 marks)
 "Compute ways(n) in a number of operations that grows linearly with n
 (at most n additions, no function calls), using constant extra memory, giving
 results identical to the original for all n, and making n = 1,000 and
 n = 10,000 run in under 0.01 s with no RecursionError."
 Derived from the limitation: exponential calls and the depth limit of 1000.

C. REVISED SOLUTION (4 marks)
 What changed: recursion (top-down, recomputation) is replaced by a loop that
 builds the answers from small n upwards (bottom-up dynamic programming).
 Property exploited: overlapping sub-problems + optimal substructure: ways(n)
 depends only on ways(n-1) and ways(n-2), so only the last TWO values need to be
 stored, and each is computed exactly once.
 Extra memory: none (O(1) auxiliary space: two integers; the big integers
 themselves grow with n, which is unavoidable because the answer does).
 New trade-offs: (1) loses the direct "mirror of the mathematical definition"
 readability of the recursion; (2) it computes ALL smaller values on the way
 up, even if only one value is wanted (fine here, since it is needed anyway);
 (3) an arbitrary-size cache of previous answers is not kept, so asking for
 many different n values repeats the loop (a table or memoisation would answer
 repeated queries in O(1)).

 Pseudocode
   function ways(n):
       prev <- 1            // ways(0)
       cur  <- 1            // ways(1)
       repeat for k from 2 to n:
           (prev, cur) <- (cur, prev + cur)
       return cur

 Flowchart:  Start -> prev=1, cur=1 -> [k = 2] -> k <= n ? -- no --> return cur
             yes -> (prev, cur) = (cur, prev+cur) -> k = k + 1 -> back to "k <= n ?"

D. PREDICTION (1 mark)
 Expected: original calls = 2*ways(n) - 1, e.g. 2,692,537 for n = 30 and about
 7 million for n = 32; redesign operations = n - 1 (29 for n = 30); results
 identical; the redesign completes n = 1000 (and 10,000) instantly and the original cannot.
 Measure of success: operation/call counts (primary evidence) and times.

E. IMPLEMENT AND VALIDATE (2 marks): see validate_and_measure() above; results
 in q7_results.csv. The counts match the prediction exactly; the redesign is
 hundreds of thousands of times faster at n = 30 and works for n = 10,000.

F. CRITICAL EVALUATION (2 marks)
 Did the redesign meet the objective?  Yes: linear operations (n - 1), O(1)
 auxiliary space, identical answers for n = 0..30, no recursion limit issues.
 Limitations: Python integers grow, so the n-th addition costs O(n) bit-
 operations for large values; the true cost for very large n is O(n^2) bit
 operations (still tiny for n = 10,000). A fast-doubling / matrix method would
 compute ways(n) in O(log n) multiplications, which would be better for
 enormous n.
 Situations where the original solution may still be preferable: when n is
 very small (<= 20) and clarity matters more than speed; when the code is used
 for teaching recursion or as a reference for testing the fast version; or
 when the recursive definition is itself the specification (it is the easiest
 to verify by inspection).
 A redesign that does not outperform the original is not automatically
 unsuccessful if the reasons are explained: for tiny n the loop and the
 recursion take about the same time, so the benefit shows only as n grows.
=============================================================================
"""
