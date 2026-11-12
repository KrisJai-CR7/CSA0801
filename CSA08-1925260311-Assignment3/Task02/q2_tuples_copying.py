"""
Q2 - Tuples, Mutability and Copying (City Bus-Stop Map)
"""
import copy
import sys
import time

# ============================================ the given program (TODO 1 done)
rows, cols = 3, 4

bad = [[0] * cols] * rows            # every row is the SAME list object
bad[0][1] = 7

# TODO 1 (completed): rows x cols grid of zeros, every row a separate list
good = [[0] * cols for _ in range(rows)]
good[0][1] = 7

print("bad :", bad)
print("good:", good)
print(bad[0] is bad[1], good[0] is good[1])

# Tuples are immutable, so they can be used as dictionary keys
stops = {(13.0827, 80.2707): "Chennai Central", (13.0418, 80.2341): "T. Nagar"}
print(stops[(13.0418, 80.2341)])

print("\n--- list as dictionary key ---")
try:
    stops[[13.0418, 80.2341]] = "T. Nagar"
except TypeError as e:
    print("TypeError:", e)


# ========================================================= more experiments
def main():
    print("\n--- is / id() : the bug and its correction ---")
    print("bad rows ids :", [id(r) for r in bad], " -> all equal:",
          len({id(r) for r in bad}) == 1)
    print("good rows ids:", [id(r) for r in good], " -> all different:",
          len({id(r) for r in good}) == rows)

    print("\n--- aliasing, shallow copy and deep copy ---")
    original = [[1, 2], [3, 4]]
    alias = original                       # same object
    shallow1 = copy.copy(original)         # new outer list, same inner lists
    shallow2 = original[:]                 # slicing = shallow copy
    deep = copy.deepcopy(original)         # everything copied
    original[0][0] = 99                    # change an INNER list
    original.append([5, 6])                # change the OUTER list
    print("original      :", original)
    print("alias         :", alias, "  alias is original:", alias is original)
    print("copy.copy     :", shallow1, "  inner shared:", shallow1[0] is original[0])
    print("slice [:]     :", shallow2, "  inner shared:", shallow2[0] is original[0])
    print("copy.deepcopy :", deep, "  inner shared:", deep[0] is original[0])

    print("\n--- function that changes a list argument ---")

    def add_zone(zones):
        zones.append("Zone-9")             # mutates the caller's list

    def add_zone_safe(zones):
        zones = zones + ["Zone-9"]         # rebinding: new list, caller unchanged
        return zones

    caller = ["Zone-1"]
    add_zone(caller)
    print("after add_zone      :", caller)
    caller2 = ["Zone-1"]
    new = add_zone_safe(caller2)
    print("after add_zone_safe :", caller2, "| returned:", new)

    print("\n--- unpacking tuples in a for loop ---")
    for (lat, lon), name in stops.items():
        print(f"{name:16} lat={lat:<8} lon={lon}")
    stop_list = [("Chennai Central", 13.0827, 80.2707), ("T. Nagar", 13.0418, 80.2341)]
    for name, lat, lon in stop_list:
        print(name, "->", (lat, lon))

    print("\n--- counting boarding per zone with a (row, col) key ---")
    board = {}
    for z in [(0, 1), (0, 1), (2, 3)]:
        board[z] = board.get(z, 0) + 1
    print(board)

    print("\n--- sys.getsizeof: list vs tuple of 1,000,000 values ---")
    lst = list(range(1_000_000))
    tup = tuple(lst)
    print(f"list : {sys.getsizeof(lst):>10,} bytes")
    print(f"tuple: {sys.getsizeof(tup):>10,} bytes (the int objects are shared and "
          f"not counted by either)")

    print("\n--- time creating and indexing (3 runs, average) ---")
    def avg(f, n=3):
        t = []
        for _ in range(n):
            t0 = time.perf_counter(); f(); t.append(time.perf_counter() - t0)
        return sum(t) / n
    print(f"create list : {avg(lambda: list(range(1_000_000))):.5f} s")
    print(f"create tuple: {avg(lambda: tuple(range(1_000_000))):.5f} s")
    print(f"index list x1,000,000 : {avg(lambda: [lst[i] for i in range(1_000_000)]):.5f} s")
    print(f"index tuple x1,000,000: {avg(lambda: [tup[i] for i in range(1_000_000)]):.5f} s")

    print("\n--- a list stored inside a tuple ---")
    t = ([1, 2], "bus")
    t[0].append(3)                          # allowed: the LIST is mutable
    print("after t[0].append(3):", t)
    try:
        t[0] = [9]                          # not allowed: rebinding a slot
    except TypeError as e:
        print("t[0] = [9] ->", type(e).__name__ + ":", e)
    try:
        {t: 1}
    except TypeError as e:
        print("tuple containing a list as a key ->", type(e).__name__ + ":", e)

    print("\n--- alternative: sparse dictionary grid ---")
    sparse = {}
    for z in [(0, 1), (0, 1), (2, 3)]:
        sparse[z] = sparse.get(z, 0) + 1
    dense = [[0] * 1000 for _ in range(1000)]
    print("dense 1000 x 1000 list of lists: 1,000,000 cells ->",
          f"{sys.getsizeof(dense) + sum(sys.getsizeof(r) for r in dense):,} bytes")
    print("sparse dict with 3 non-empty zones ->", f"{sys.getsizeof(sparse):,} bytes")


if __name__ == "__main__":
    main()


"""
EXPECTED OUTPUT of the given program (matches the brief)
bad : [[0, 7, 0, 0], [0, 7, 0, 0], [0, 7, 0, 0]]
good: [[0, 7, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
True False
T. Nagar

DESIGN & ANALYSIS
 - Tuples can be dictionary keys but lists cannot: a key must be HASHABLE (its
   hash must never change while it is in the dict). A tuple of immutable values
   cannot change, so its hash is stable. A list is mutable: changing it would
   change its hash and the dictionary would lose track of the entry, so Python
   refuses: TypeError: unhashable type: 'list'. (A tuple that CONTAINS a list is
   also unhashable.)
 - Memory diagram of [[0] * 3] * 3  (rows are references to ONE list):
       bad ──► [ ref, ref, ref ]
                  │    │    │
                  └────┴────┴──► [0, 0, 0]       (one single inner list)
   Corrected grid [[0] * 3 for _ in range(3)]:
       good ─► [ ref, ref, ref ]
                  │    │    └──► [0, 0, 0]   (3 separate inner lists)
                  │    └───────► [0, 0, 0]
                  └────────────► [0, 0, 0]
   The multiplication copies the REFERENCE, not the object, so one update shows
   in every row.
 - Shallow copy is enough when the elements are immutable (numbers, strings,
   tuples) or you will only replace/add/remove items of the outer list. A deep
   copy is needed when elements are mutable containers (a grid, a list of lists)
   and the copy must be completely independent of the original.
 - A function that changes a list argument changes the caller's list because
   the parameter is a reference to the SAME object (names are passed by
   assignment); append/sort/[i]= mutate that object. Rebinding the parameter
   (zones = zones + [...]) creates a new list and leaves the caller untouched.

CONCLUSION: use a tuple for a fixed record (a coordinate pair, a database row)
 that must not change, for dictionary keys and set members, and to return
 several values; it needs less memory and signals intent. Immutability protects
 you from accidental changes through aliases or called functions and keeps hash
 keys valid. Remember it is shallow: a list stored inside a tuple can still change.

ALTERNATIVE CONCEPT: dictionary keyed by (row, col) holding only non-empty zones
 - Access time: O(1) on average for both designs (index arithmetic for the list
   of lists; hashing for the dict).
 - Space: list of lists O(rows x cols) even if almost all zones are empty;
   the dictionary O(number of non-empty zones) but with a bigger cost per entry.
   Choose the dict for large sparse city grids and the list of lists when most
   zones are used or when whole rows must be processed quickly.
"""
