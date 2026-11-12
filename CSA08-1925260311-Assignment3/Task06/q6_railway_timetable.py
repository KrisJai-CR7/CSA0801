"""
Q6 - Nested Data: A Railway Timetable
timetable = { train_no: { "name": str,
                          "stops": [ (station, arrival, departure), ... ],
                          "days":  {"Mon", "Tue", ...} } }
"""
import random
import sys
import time

ALL_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

timetable = {
    12601: {"name": "Chennai Mail",
            "stops": [("Chennai", "--", "20:00"), ("Katpadi", "22:10", "22:12"),
                      ("Bengaluru", "01:15", "01:25"), ("Hubballi", "09:30", "--")],
            "days": {"Mon", "Wed", "Fri"}},
    12602: {"name": "Bengaluru Express",
            "stops": [("Chennai", "--", "06:00"), ("Katpadi", "08:00", "08:02"),
                      ("Bengaluru", "11:00", "--")],
            "days": set(ALL_DAYS)},
    12603: {"name": "Cheran Express",
            "stops": [("Coimbatore", "--", "22:15"), ("Salem", "00:50", "00:55"),
                      ("Katpadi", "03:30", "03:35"), ("Chennai", "06:10", "--")],
            "days": {"Tue", "Thu", "Sun"}},
    12604: {"name": "Pallavan Express",
            "stops": [("Chennai", "--", "15:30"), ("Villupuram", "17:50", "17:52"),
                      ("Trichy", "20:45", "20:50"), ("Karaikudi", "23:00", "--")],
            "days": set(ALL_DAYS)},
    12605: {"name": "Kovai Express",
            "stops": [("Chennai", "--", "14:10"), ("Katpadi", "16:15", "16:17"),
                      ("Salem", "18:30", "18:35"), ("Coimbatore", "21:50", "--")],
            "days": {"Mon", "Tue", "Wed", "Thu", "Fri"}},
}


# ------------------------------------------------------------- queries
def trains_at(tt, station, day):
    """Trains that stop at `station` on `day`, sorted by departure there."""
    found = []
    for no, info in tt.items():
        if day not in info["days"]:
            continue
        for st, arr, dep in info["stops"]:
            if st == station:
                found.append((no, info["name"], arr, dep))
    # terminal stops have no departure ("--"): treat them as arrival time
    return sorted(found, key=lambda r: r[3] if r[3] != "--" else r[2])


def build_index(tt):
    """station -> list of (train_no, arrival, departure, days)."""
    index = {}
    for no, info in tt.items():
        for st, arr, dep in info["stops"]:
            index.setdefault(st, []).append((no, arr, dep, info["days"]))
    return index


def trains_at_indexed(tt, index, station, day):
    found = [(no, tt[no]["name"], arr, dep)
             for no, arr, dep, days in index.get(station, []) if day in days]
    return sorted(found, key=lambda r: r[3] if r[3] != "--" else r[2])


def print_timetable(tt):
    for no in sorted(tt):
        info = tt[no]
        days = ",".join(d for d in ALL_DAYS if d in info["days"])
        print(f"\n{no}  {info['name']}   runs: {days}")
        print(f"  {'Station':<12}{'Arr':>7}{'Dep':>7}")
        for st, arr, dep in info["stops"]:
            print(f"  {st:<12}{arr:>7}{dep:>7}")


def flat_list(tt):
    """Alternative design: one flat list of (train, station, arr, dep, days)."""
    return [(no, st, arr, dep, info["days"])
            for no, info in tt.items() for st, arr, dep in info["stops"]]


def trains_at_flat(flat, names, station, day):
    found = [(no, names[no], arr, dep) for no, st, arr, dep, days in flat
             if st == station and day in days]
    return sorted(found, key=lambda r: r[3] if r[3] != "--" else r[2])


def make_timetable(n, seed=0):
    rnd = random.Random(seed)
    stations = [f"S{i:03d}" for i in range(200)]
    tt = {}
    for t in range(n):
        k = rnd.randint(8, 20)
        chosen = rnd.sample(stations, k)
        stops = []
        for i, st in enumerate(chosen):
            minute = (i * 30) % 1440
            stops.append((st, f"{minute // 60:02d}:{minute % 60:02d}",
                          f"{(minute + 2) // 60 % 24:02d}:{(minute + 2) % 60:02d}"))
        tt[10000 + t] = {"name": f"Train {t}", "stops": stops,
                         "days": set(rnd.sample(ALL_DAYS, rnd.randint(3, 7)))}
    return tt


def deep_size(obj, seen=None):
    """Approximate memory: sys.getsizeof of the containers and their contents."""
    seen = set() if seen is None else seen
    if id(obj) in seen:
        return 0
    seen.add(id(obj))
    size = sys.getsizeof(obj)
    if isinstance(obj, dict):
        size += sum(deep_size(k, seen) + deep_size(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(deep_size(i, seen) for i in obj)
    return size


if __name__ == "__main__":
    print_timetable(timetable)

    print("\n--- query: trains stopping at Katpadi on Wed, sorted by departure ---")
    for no, name, arr, dep in trains_at(timetable, "Katpadi", "Wed"):
        print(f"  {no} {name:<18} arr {arr}  dep {dep}")
    print("expected by hand: 12602 (08:02), 12605 (16:17), 12601 (22:12) ->",
          [r[0] for r in trains_at(timetable, "Katpadi", "Wed")])

    idx = build_index(timetable)
    print("indexed gives same answer:",
          trains_at(timetable, "Katpadi", "Wed") ==
          trains_at_indexed(timetable, idx, "Katpadi", "Wed"))

    print("\n--- edge cases ---")
    print("unknown station            :", trains_at(timetable, "Atlantis", "Wed"),
          trains_at_indexed(timetable, idx, "Atlantis", "Wed"))
    print("train 12601 not running Tue:", [r[0] for r in trains_at(timetable, "Katpadi", "Tue")],
          "(12601 is absent)")

    print("\nDeparture time of the THIRD station of train 12601:",
          timetable[12601]["stops"][2][2], " <- timetable[12601]['stops'][2][2]")

    print(f"\n{'trains':>7} {'stops':>8} {'scan s/query':>13} {'indexed s/query':>16} "
          f"{'index build s':>14} {'index extra bytes':>18}")
    for n in (100, 1_000, 10_000):
        tt = make_timetable(n, seed=n)
        total_stops = sum(len(v["stops"]) for v in tt.values())
        q = 30
        stations = [f"S{i:03d}" for i in range(0, 200, 7)][:q]
        t0 = time.perf_counter()
        for s in stations:
            a = trains_at(tt, s, "Mon")
        t_scan = (time.perf_counter() - t0) / q
        t0 = time.perf_counter(); idx = build_index(tt); t_build = time.perf_counter() - t0
        t0 = time.perf_counter()
        for s in stations:
            b = trains_at_indexed(tt, idx, s, "Mon")
        t_idx = (time.perf_counter() - t0) / q
        assert trains_at(tt, stations[-1], "Mon") == trains_at_indexed(tt, idx, stations[-1], "Mon")
        # extra memory: only the NEW lists/tuples of the index (stops/days are shared)
        extra = sys.getsizeof(idx) + sum(sys.getsizeof(v) + sum(sys.getsizeof(e) for e in v)
                                         for v in idx.values())
        print(f"{n:>7,} {total_stops:>8,} {t_scan:>13.6f} {t_idx:>16.6f} "
              f"{t_build:>14.4f} {extra:>18,}")
        names = {k: v["name"] for k, v in tt.items()}
        flat = flat_list(tt)
        t0 = time.perf_counter()
        for s in stations:
            c = trains_at_flat(flat, names, s, "Mon")
        t_flat = (time.perf_counter() - t0) / q
        print(f"{'':>7} flat-list scan: {t_flat:.6f} s/query "
              f"(same answers: {c == trains_at(tt, stations[-1], 'Mon')})")


"""
DESIGN & ANALYSIS
Nested structure (diagram)
   timetable (dict)  train_no ─► info (dict)
        info["name"]  ─► str
        info["stops"] ─► list ─► (station, arrival, departure)  tuples (fixed records)
        info["days"]  ─► set of day names
 Expression for the departure time of the third station of a train:
        timetable[12601]["stops"][2][2]        # train -> "stops" -> 3rd tuple -> departure

 Why each part:
  - dictionary keyed by train number: unique, immutable key, O(1) lookup by train.
  - info is a dictionary: fields with names (name, stops, days) - self-describing.
  - stops is a LIST: ORDER matters (the route sequence) and it may need to grow.
  - each stop is a TUPLE: a fixed record (station, arrival, departure) that
    should not change by accident and is lighter than a dict.
  - days is a SET: no duplicates, order irrelevant, and "day in days" is O(1).

 Work for one station query (no index): visit all T trains and all their stops:
  O(total stops S) = O(T x average stops). Every query repeats it.
 Index (station -> list of (train, arr, dep, days)): built once in O(S); a query
  looks up the station in O(1) average and examines only the m trains that
  stop there -> O(m + m log m) including the sort.

CONCLUSION: the index makes each query faster because the dictionary jumps
 straight to the trains of that station instead of scanning every stop. The
 trade-off is EXTRA MEMORY (one more entry per stop, see the table) plus build
 time, and the index must be rebuilt/updated whenever the timetable changes
 (risk of stale data). Worth it when queries are many and the timetable changes rarely.

ALTERNATIVE CONCEPT: one flat list of (train, station, arrival, departure, days)
 - Time per query: O(total stops S) - every tuple is checked, same as the
   unindexed nested scan (measured above, no better).
 - Time per query with nested dictionaries + station index: O(trains at the station).
 - Space: flat list O(S) (days repeated in every tuple unless shared); nested
   dictionaries O(S) + O(number of trains) overhead for names/days; index adds
   another O(S) references. The flat list is simple and compact but slow to
   query; nested + index is fast but uses more memory.
"""
