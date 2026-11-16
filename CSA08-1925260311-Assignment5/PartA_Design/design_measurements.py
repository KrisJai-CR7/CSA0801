"""
Measurements that support the 'Alternative Concept and Complexity Analysis' answers of Part A
  (1) A1.3  CSV versus SQL for three typical questions of the board
  (2) A2    dropping / forward-filling / median-filling missing readings
  (3) A4    print versus logging (cost of thousands of calls, and switching them off)
Run:  python design_measurements.py
"""
import csv
import io
import logging
import statistics
import sys
import tempfile
import time
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import pandas as pd
from common import aqlib


def best(fn, reps=3):
    b = None
    for _ in range(reps):
        t0 = time.perf_counter(); out = fn(); dt = time.perf_counter() - t0
        b = dt if b is None else min(b, dt)
    return out, b


def part1(tmp):
    print("(1) A1.3  CSV scan vs pandas read_csv vs SQL (12 stations x 365 days = 105,120 rows; ms, best of 3)")
    rows = aqlib.generate_rows(12, 365, seed=1, dirty=False)
    path = Path(tmp) / "year.csv"
    aqlib.write_csv(rows, path)
    clean = [(r[0], r[1], int(r[2]), float(r[3]), float(r[4]), float(r[5]), float(r[6])) for r in rows]
    con = aqlib.build_db(clean)
    con.execute("CREATE INDEX idx ON readings(station_id, day)")

    def q1_csv():
        t = n = 0
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                if r["station"] == "Adyar" and r["date"].startswith("2026-10"):
                    t += float(r["pm25"]); n += 1
        return t / n

    def q1_pandas():
        df = pd.read_csv(path)
        return df[(df.station == "Adyar") & df.date.str.startswith("2026-10")].pm25.mean()

    def q1_sql():
        return con.execute("SELECT AVG(pm25) FROM readings r JOIN stations s USING(station_id) WHERE s.name='Adyar' "
                           "AND day BETWEEN '2026-10-01' AND '2026-10-31'").fetchone()[0]

    def q2_csv():
        acc = {}
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                a = acc.setdefault(r["station"], [0.0, 0]); a[0] += float(r["pm25"]); a[1] += 1
        return max(acc, key=lambda k: acc[k][0] / acc[k][1])

    def q2_pandas():
        return pd.read_csv(path).groupby("station").pm25.mean().idxmax()

    def q2_sql():
        return con.execute("SELECT s.name FROM readings r JOIN stations s USING(station_id) GROUP BY s.name "
                           "ORDER BY AVG(pm25) DESC LIMIT 1").fetchone()[0]

    def q3_csv():
        acc = {}
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                a = acc.setdefault(r["hour"], [0.0, 0]); a[0] += float(r["pm25"]); a[1] += 1
        return max(acc, key=lambda k: acc[k][0] / acc[k][1])

    def q3_pandas():
        return pd.read_csv(path).groupby("hour").pm25.mean().idxmax()

    def q3_sql():
        return con.execute("SELECT hour FROM readings GROUP BY hour ORDER BY AVG(pm25) DESC LIMIT 1").fetchone()[0]

    print(f"    {'question':<44}{'CSV loop':>10}{'pandas':>9}{'SQL':>9}")
    for name, fns in (("Q1 average PM2.5 of Adyar in October", (q1_csv, q1_pandas, q1_sql)),
                      ("Q2 station with highest mean PM2.5", (q2_csv, q2_pandas, q2_sql)),
                      ("Q3 hour of the day with the worst air", (q3_csv, q3_pandas, q3_sql))):
        res = [best(f) for f in fns]
        print(f"    {name:<44}{res[0][1] * 1000:>10.1f}{res[1][1] * 1000:>9.1f}{res[2][1] * 1000:>9.1f}"
              f"   answers: {[str(round(float(r[0]), 2)) if not isinstance(r[0], str) else r[0] for r in res]}")


def part2():
    print("\n(2) A2   missing readings: drop vs forward fill vs median fill (12 stations x 365 days, dirty data)")
    raw = aqlib.generate_rows(12, 365, seed=6)
    cleaned, rep = aqlib.clean_rows(raw)            # forward fill (limit 3) already applied
    # (a) drop: no filling - use only valid values
    seen, groups_drop = set(), {}
    parsed = []
    for r in raw:
        name = " ".join(r[0].split()).title(); day = aqlib.parse_date(r[1])
        key = (name, day, r[2])
        if key in seen:
            continue
        seen.add(key)
        v, kind = aqlib.parse_number(r[3], 0, aqlib.PM_MAX)
        parsed.append((name, day, v))

    def drop():
        g = {}
        for n, d, v in parsed:
            if v is not None:
                g.setdefault((n, d), []).append(v)
        return {k: sum(v) / len(v) for k, v in g.items()}

    def ffill():
        g = {}
        for r in cleaned:
            if r[3] is not None:
                g.setdefault((r[0], r[1]), []).append(r[3])
        return {k: sum(v) / len(v) for k, v in g.items()}

    def median_fill():
        med = {}
        by_station = {}
        for n, d, v in parsed:
            if v is not None:
                by_station.setdefault(n, []).append(v)
        med = {n: statistics.median(v) for n, v in by_station.items()}      # sorts: O(n log n)
        g = {}
        for n, d, v in parsed:
            g.setdefault((n, d), []).append(med[n] if v is None else v)
        return {k: sum(v) / len(v) for k, v in g.items()}

    (a, ta), (b, tb), (c, tc) = best(drop), best(ffill), best(median_fill)
    keys = a.keys() & b.keys() & c.keys()
    print(f"    time: drop {ta * 1000:.0f} ms | forward fill {tb * 1000:.0f} ms (the cleaning rows are re-used) | "
          f"median fill {tc * 1000:.0f} ms")
    print(f"    station-days compared: {len(keys):,}")
    print(f"    mean |difference| of the daily mean vs drop: forward fill "
          f"{sum(abs(a[k] - b[k]) for k in keys) / len(keys):.3f}, median fill "
          f"{sum(abs(a[k] - c[k]) for k in keys) / len(keys):.3f} ug/m3; "
          f"largest: forward fill {max(abs(a[k] - b[k]) for k in keys):.2f}, median fill {max(abs(a[k] - c[k]) for k in keys):.2f}")
    print(f"    readings lost if dropped: {sum(1 for _, _, v in parsed if v is None):,} of {len(parsed):,} "
          f"({100 * sum(1 for _, _, v in parsed if v is None) / len(parsed):.1f}%)")


def part4():
    print("\n(3) A4   200,000 debugging calls: print vs logging (microseconds per call)")
    N = 200_000
    def run(label, fn):
        t0 = time.perf_counter()
        for i in range(N):
            fn(i)
        dt = time.perf_counter() - t0
        print(f"    {label:<48}{dt / N * 1e6:>8.2f} us/call   total {dt:.2f} s")
    buf = io.StringIO()
    with redirect_stdout(buf):
        t0 = time.perf_counter()
        for i in range(N):
            print("value", i)
        dt = time.perf_counter() - t0
    print(f"    {'print() to a buffer (terminal would be slower)':<48}{dt / N * 1e6:>8.2f} us/call   total {dt:.2f} s")
    log_file = Path(tempfile.mkdtemp()) / "debug.log"
    lg = logging.getLogger("aq"); lg.propagate = False
    h = logging.FileHandler(log_file); lg.addHandler(h)
    lg.setLevel(logging.DEBUG)
    run("logging.debug(), level DEBUG, writes to a file", lambda i: lg.debug("value %d", i))
    lg.setLevel(logging.WARNING)
    run("logging.debug(), level WARNING (switched off)", lambda i: lg.debug("value %d", i))
    DEBUG = False
    run("if DEBUG: print(...)  with DEBUG = False", lambda i: print("value", i) if DEBUG else None)
    run("no debugging call at all (empty function)", lambda i: None)
    h.close()


if __name__ == "__main__":
    tmp = tempfile.mkdtemp()
    part1(tmp)
    part2()
    part4()
