"""
Q4 - Sets: Elective Registration Clash Detection
"""
import random
import time

# ============================================== the given program (TODO 1 done)
ai_elective = {"192311001", "192311004", "192311007", "192311009"}
iot_elective = {"192311002", "192311004", "192311009", "192311010"}
all_students = {f"1923110{i:02d}" for i in range(1, 11)}

# TODO 1 (completed): set OPERATORS only
both = ai_elective & iot_elective                    # intersection: clash
exactly_one = ai_elective ^ iot_elective             # symmetric difference
neither = all_students - (ai_elective | iot_elective)   # difference of the union

print("clash :", sorted(both))
print("exactly one:", sorted(exactly_one))
print("neither :", sorted(neither))


# ===================================================== same with set methods
def classify_methods(a, b, everyone):
    both_m = a.intersection(b)
    one_m = a.symmetric_difference(b)
    neither_m = everyone.difference(a.union(b))
    return both_m, one_m, neither_m


# ========================================== alternatives for common students
def common_nested(a, b):
    """Lists + nested loops: O(n * m)."""
    out = []
    for x in a:
        for y in b:
            if x == y:
                out.append(x)
                break
    return out


def common_sorted_walk(a, b):
    """Sort both lists and walk through them: O(n log n + m log m)."""
    a, b = sorted(a), sorted(b)
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append(a[i]); i += 1; j += 1
        elif a[i] < b[j]:
            i += 1
        else:
            j += 1
    return out


def regs(n, start=0):
    return [f"{192300000 + start + i}" for i in range(n)]


if __name__ == "__main__":
    print("\nset METHODS give the same result:",
          classify_methods(ai_elective, iot_elective, all_students) ==
          (both, exactly_one, neither))

    # ---------- hand verification of a small case
    a, b = {"1", "2", "3"}, {"3", "4"}
    print("\nHand check A={1,2,3} B={3,4}: A&B={3}, A^B={1,2,4}, A-B={1,2}, A|B={1,2,3,4}")
    print("  program :", a & b, a ^ b, a - b, a | b)

    # ---------- edge cases
    empty = set()
    print("\nEmpty elective A=empty, B=iot  :", empty & iot_elective,
          empty ^ iot_elective, sorted(all_students - (empty | iot_elective)))
    print("Both electives empty           :", empty & empty, empty ^ empty)
    same = set(ai_elective)
    print("Identical electives            : clash =", sorted(ai_elective & same),
          "| exactly one =", sorted(ai_elective ^ same), "(empty)")
    print("duplicates removed by a set    :", set(["a", "b", "a", "a"]))
    print("tuple in a set:", {(1, 2), (1, 2)}, end=" | ")
    try:
        {[1, 2]}
    except TypeError as e:
        print("list in a set ->", e)

    # ---------- x in list vs x in set
    print(f"\n{'size':>10} {'x in list s':>13} {'x in set s':>12}   "
          "(1,000 lookups of a MISSING register number)")
    for n in (10_000, 100_000, 1_000_000):
        lst = regs(n)
        st = set(lst)
        missing = "999999999"
        t0 = time.perf_counter()
        for _ in range(1000):
            missing in lst
        t_list = time.perf_counter() - t0
        t0 = time.perf_counter()
        for _ in range(1000):
            missing in st
        t_set = time.perf_counter() - t0
        print(f"{n:>10,} {t_list:>13.5f} {t_set:>12.6f}")

    # ---------- common students: nested loops vs sorted walk vs &
    print(f"\n{'n = m':>8} {'nested loops s':>15} {'sorted walk s':>14} {'& on sets s':>12} same")
    for n in (1_000, 3_000, 10_000):
        a_list = regs(n)
        b_list = regs(n, start=n // 2)             # half overlap
        t0 = time.perf_counter(); r1 = common_nested(a_list, b_list); t1 = time.perf_counter() - t0
        t0 = time.perf_counter(); r2 = common_sorted_walk(a_list, b_list); t2 = time.perf_counter() - t0
        t0 = time.perf_counter(); r3 = set(a_list) & set(b_list); t3 = time.perf_counter() - t0
        print(f"{n:>8,} {t1:>15.5f} {t2:>14.5f} {t3:>12.5f} "
              f"{set(r1) == set(r2) == r3}")
    n = 1_000_000
    a_list, b_list = regs(n), regs(n, start=n // 2)
    t0 = time.perf_counter(); r3 = set(a_list) & set(b_list); t3 = time.perf_counter() - t0
    print(f"{n:>8,} {'(skipped: ~10^12 steps)':>15} {'':>14} {t3:>12.5f}  common = {len(r3):,}")


"""
EXPECTED OUTPUT (matches the program):
clash : ['192311004', '192311009']
exactly one: ['192311001', '192311002', '192311007', '192311010']
neither : ['192311003', '192311005', '192311006', '192311008']

DESIGN & ANALYSIS (Venn diagrams, A = AI elective, B = IoT elective, U = all students)
   both (A & B)            : the OVERLAP of the two circles          -> 004, 009
   exactly one (A ^ B)     : both circles WITHOUT the overlap        -> 001, 007, 002, 010
   neither (U - (A | B))   : the area of U OUTSIDE both circles     -> 003, 005, 006, 008
   union (A | B)           : both circles including the overlap
   A - B                   : circle A without the overlap            -> 001, 007

 - Sets remove duplicates automatically because members are stored in a hash
   table: adding an element that is already equal (same hash and ==) changes
   nothing, so each value can appear only once.
 - x in s is faster for a set than for a list: a set computes hash(x) and checks
   one slot (O(1) average); a list compares x with the items one by one (O(n)).
 - Sets cannot contain lists, but can contain tuples: set members must be
   hashable, i.e. immutable. A list can change (so would its hash); a tuple of
   immutable items cannot.

CONCLUSION: convert a list to a set before processing when you need fast
 membership tests, duplicate removal or set algebra (common / different items).
 Information lost: the ORDER of the items, the DUPLICATES (how many times
 each appeared) and the ability to index/slice; only hashable items are allowed.

ALTERNATIVE CONCEPT & COMPLEXITY (electives of n and m students)
 - Lists + nested loops: time O(n * m), space O(1) extra.
 - Sort both lists and walk together: O(n log n + m log m) for the sorts + O(n + m)
   for the walk; space O(1) extra if sorted in place (O(n + m) here for copies).
 - Sets and &: build sets O(n + m), intersection O(min(n, m)) on average ->
   O(n + m) on average in total; space O(n + m) for the hash tables.
 - The measured times follow this: nested loops grow about 9x when n triples
   (quadratic), the sorted walk and & grow roughly linearly.
"""
