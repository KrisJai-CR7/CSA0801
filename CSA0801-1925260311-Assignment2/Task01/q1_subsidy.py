"""
Q1 - Decisions with Many Boundaries (State Electricity Subsidy Eligibility)

Rule
  * units <= 100                  -> full subsidy
  * 101 <= units <= 200           -> partial subsidy, only with a ration card
  * units > 200                   -> no subsidy, unless a member is above 80 years
"""
import time


# ---------------------------------------------------------------- PREDICTIONS
# (units, ration_card, has_80plus, expected result by the written rule)
# Written BEFORE running anything.
HOUSEHOLDS = [
    (100, True,  False, "FULL"),      # boundary: 100 is still "100 or less"
    (101, True,  False, "PARTIAL"),   # boundary: first unit of the partial slab
    (101, False, False, "NONE"),      # partial slab but no ration card
    (200, True,  False, "PARTIAL"),   # boundary: last unit of the partial slab
    (200, False, True,  "NONE"),      # 80+ member does not help in the slab 101-200
    (201, True,  False, "NONE"),      # boundary: ration card does not help above 200
    (201, False, True,  "SPECIAL"),   # boundary: first unit above 200, 80+ member
    (50,  True,  True,  "FULL"),      # low usage: ration card / elder irrelevant
]


# ------------------------------------------- 1. SEPARATE if STATEMENTS (buggy)
def subsidy_separate_if(units, ration, elder):
    """Developer's version: independent if's, so several can fire together."""
    result = []
    if units <= 100:
        result.append("FULL")
    if units <= 200 and ration:          # BUG: no lower bound (units > 100)
        result.append("PARTIAL")
    if units > 200 and elder:
        result.append("SPECIAL")
    return result if result else ["NONE"]


# ----------------------------------------------- 2. if-elif-else (corrected)
def subsidy_elif(units, ration, elder):
    """Exactly one branch runs, so exactly one result is possible."""
    if units <= 100:
        return "FULL"
    elif units <= 200:                    # implies 101 <= units <= 200
        return "PARTIAL" if ration else "NONE"
    else:                                 # implies units > 200
        return "SPECIAL" if elder else "NONE"


# --------------------------------------- chained comparison form (as in brief)
def subsidy_chained(units, ration, elder):
    if units <= 100:
        return "FULL"
    if 101 <= units <= 200 and ration:
        return "PARTIAL"
    if units > 200 and elder:
        return "SPECIAL"
    return "NONE"


# -------------------------------------------------- DESIGN DECISION variants
def subsidy_nested(units, ration, elder):
    """Nested ifs: mirrors the English rule, but gets deep as slabs grow."""
    if units <= 100:
        return "FULL"
    else:
        if units <= 200:
            if ration:
                return "PARTIAL"
            return "NONE"
        else:
            if elder:
                return "SPECIAL"
            return "NONE"


# -------------------------------------------------- ALTERNATIVE 1: match-case
def subsidy_match(units, ration, elder):
    """match-case (Python 3.10+) with guards."""
    match units:
        case u if u <= 100:
            return "FULL"
        case u if u <= 200:
            return "PARTIAL" if ration else "NONE"
        case _:
            return "SPECIAL" if elder else "NONE"


# --------------------------------- ALTERNATIVE 2: (upper_limit, decision) table
SLABS = [
    (100, lambda ration, elder: "FULL"),
    (200, lambda ration, elder: "PARTIAL" if ration else "NONE"),
    (float("inf"), lambda ration, elder: "SPECIAL" if elder else "NONE"),
]


def subsidy_lookup(units, ration, elder):
    for upper, decide in SLABS:           # linear search: O(k) for k slabs
        if units <= upper:
            return decide(ration, elder)


def main():
    print("=" * 78)
    print("Q1  PREDICTION vs OBSERVED (separate-if vs if-elif-else)")
    print("=" * 78)
    print(f"{'units':>5} {'ration':>6} {'80+':>5} | {'predicted':<9} | "
          f"{'separate if':<16} | {'if-elif-else':<12} | ok?")
    print("-" * 78)
    all_ok = True
    for units, ration, elder, predicted in HOUSEHOLDS:
        sep = subsidy_separate_if(units, ration, elder)
        elf = subsidy_elif(units, ration, elder)
        ok = (elf == predicted)
        all_ok &= ok
        flag = "  <-- 2 results!" if len(sep) > 1 else ""
        print(f"{units:>5} {str(ration):>6} {str(elder):>5} | {predicted:<9} | "
              f"{'+'.join(sep):<16} | {elf:<12} | {'yes' if ok else 'NO'}{flag}")
    print("if-elif-else matches every prediction:", all_ok)

    print("\nCross-check of all correct implementations on 0..400 units:")
    funcs = [subsidy_elif, subsidy_chained, subsidy_nested,
             subsidy_match, subsidy_lookup]
    agree = True
    for u in range(0, 401):
        for r in (True, False):
            for e in (True, False):
                outs = {f(u, r, e) for f in funcs}
                if len(outs) != 1:
                    agree = False
                    print("  disagreement at", u, r, e, outs)
    print("  all five agree:", agree)

    double = sum(1 for u in range(0, 401) for r in (True, False) for e in (True, False)
                 if len(subsidy_separate_if(u, r, e)) > 1)
    print(f"  inputs where the separate-if version gives TWO subsidies: {double}")

    print("\nTiming (198,000 calls each, mixed slabs):")
    data = [(u, True, True) for u in (50, 150, 250)] * 66_000
    for f in (subsidy_elif, subsidy_nested, subsidy_match, subsidy_lookup):
        t0 = time.perf_counter()
        for u, r, e in data:
            f(u, r, e)
        print(f"  {f.__name__:<16}{time.perf_counter() - t0:.4f} s")


if __name__ == "__main__":
    main()


# =============================================================================
# EXPLANATIONS
# =============================================================================
"""
WHY separate ifs can give more than one result, but if-elif-else gives exactly one
 - Every `if` is tested independently, so each true condition runs its own
   block. A household with 100 units and a ration card satisfies
   `units <= 100` AND `units <= 200 and ration`, so it received two subsidies.
 - In an if-elif-else chain, once one condition is true Python skips every
   remaining elif/else. The order of the tests gives the lower bounds for free
   (the elif for <= 200 is only reached when units > 100).

DESIGN DECISION - nested ifs vs combined and/or
 - Chosen: flat if-elif-else on `units` (the slab), with the extra attribute
   (ration card / elder) deciding only the result inside the slab.
 - Reason: the slab is decided by `units` alone. This keeps the tree shallow, so
   adding a slab is a single new elif. Deep nesting (subsidy_nested) repeats
   "NONE" branches; long and/or chains (subsidy_chained) repeat the boundary
   numbers and are easier to get wrong when the rule changes.

ALTERNATIVE CONCEPT & COMPLEXITY (k slabs)
 - if-elif-else : up to k comparisons per decision -> time O(k), space O(1).
 - match-case with guards : guards are tested in order -> O(k) time, O(1) space.
   Gains readability, not speed.
 - Lookup list of (upper_limit, decision) : linear search -> O(k) time, O(k)
   space for the table. With the list sorted, bisect gives O(log k) time. Best
   when slabs are many or change often, because the rule becomes DATA not code.
 - For k = 3 slabs the differences are negligible (see the timings above);
   the choice is about maintainability.
"""
