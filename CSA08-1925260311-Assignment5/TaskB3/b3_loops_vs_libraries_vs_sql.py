"""
Task B3 - Loops vs Libraries vs SQL (8 marks)
Daily mean PM2.5 per station computed three ways:
   (1) plain Python loops with the csv module (+ statistics.mean)
   (2) pandas groupby
   (3) SQLite GROUP BY
B3.1 correctness on small data   B3.2 three data sizes (1, 12, 120 stations, one year)
B3.3 cProfile of the loop version   B3.4 engineering trade-off
"""
import cProfile
import csv
import io
import pstats
import sqlite3
import statistics
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import pandas as pd
from common import aqlib


# ------------------------------------------------------------------ the three methods
def daily_mean_loops(path):
    groups = {}
    with open(path, newline="", encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            groups.setdefault((rec["station"], rec["date"]), []).append(float(rec["pm25"]))
    return {k: statistics.mean(v) for k, v in groups.items()}


def daily_mean_pandas(path):
    df = pd.read_csv(path, usecols=["station", "date", "pm25"])
    s = df.groupby(["station", "date"]).pm25.mean()
    return s.to_dict()


def load_sqlite(path):
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE r (station TEXT, day TEXT, pm25 REAL)")
    with open(path, newline="", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        con.executemany("INSERT INTO r VALUES (?, ?, ?)",
                        ((x["station"], x["date"], float(x["pm25"])) for x in rd))
    con.commit()
    return con


def daily_mean_sql(con):
    return {(s, d): m for s, d, m in
            con.execute("SELECT station, day, AVG(pm25) FROM r GROUP BY station, day")}


# alternative concept: ONE pass with a running sum and count
def daily_mean_running(path):
    sums = {}
    with open(path, newline="", encoding="utf-8") as f:
        for rec in csv.DictReader(f):
            k = (rec["station"], rec["date"])
            acc = sums.get(k)
            v = float(rec["pm25"])
            if acc is None:
                sums[k] = [v, 1]
            else:
                acc[0] += v
                acc[1] += 1
    return {k: s / n for k, (s, n) in sums.items()}


def make_file(folder, stations, days, name):
    rows = aqlib.generate_rows(stations, days, seed=stations, dirty=False)
    path = Path(folder) / name
    aqlib.write_csv(rows, path)
    return path, len(rows)


def same(a, b, tol=1e-6):
    return a.keys() == b.keys() and all(abs(a[k] - b[k]) < tol for k in a)


def timeit(fn, *args, runs=1):
    best = None
    for _ in range(runs):
        t0 = time.perf_counter()
        out = fn(*args)
        dt = time.perf_counter() - t0
        best = dt if best is None else min(best, dt)
    return out, best


if __name__ == "__main__":
    tmp = tempfile.mkdtemp()

    # ------------------------------------------------------------ B3.1 correctness
    print("B3.1 CORRECTNESS ON SMALL DATA")
    tiny = Path(tmp) / "tiny.csv"
    tiny.write_text("station,date,hour,pm25\n"
                    "Adyar,2026-10-01,0,40\nAdyar,2026-10-01,1,60\nAdyar,2026-10-02,0,30\n"
                    "Guindy,2026-10-01,0,100\nGuindy,2026-10-01,1,120\nGuindy,2026-10-01,2,110\n")
    expected = {("Adyar", "2026-10-01"): 50.0, ("Adyar", "2026-10-02"): 30.0, ("Guindy", "2026-10-01"): 110.0}
    r1, r2 = daily_mean_loops(tiny), daily_mean_pandas(tiny)
    r3 = daily_mean_sql(load_sqlite(tiny))
    r4 = daily_mean_running(tiny)
    print("  hand-calculated :", expected)
    print("  loops           :", r1, "| matches:", r1 == expected)
    print("  pandas          :", {k: float(v) for k, v in r2.items()}, "| matches:", same(r2, expected))
    print("  SQL GROUP BY    :", r3, "| matches:", same(r3, expected))
    print("  running sum     :", r4, "| matches:", same(r4, expected))
    p, n = make_file(tmp, 3, 10, "small.csv")
    a, b, c = daily_mean_loops(p), daily_mean_pandas(p), daily_mean_sql(load_sqlite(p))
    print(f"  generated data ({n} rows, 30 station-days): all three agree:", same(a, b) and same(a, c))

    # ------------------------------------------------------------ B3.2 sizes
    print("\nB3.2 TIME FOR 1, 12 AND 120 STATIONS OVER A YEAR (seconds; best of 3 below 200,000 rows, one run above)")
    print(f"  {'stations':>8}{'rows':>11}{'loops':>9}{'pandas':>9}{'SQL load':>10}{'SQL query':>10}{'SQL total':>10}"
          f"{'running sum':>12}  agree")
    results = {}
    for st in (1, 12, 120):
        path, n = make_file(tmp, st, 365, f"year_{st}.csv")
        runs = 3 if n < 200_000 else 1
        a, t_loops = timeit(daily_mean_loops, path, runs=runs)
        b, t_pandas = timeit(daily_mean_pandas, path, runs=runs)
        con, t_load = timeit(load_sqlite, path, runs=1)
        c, t_query = timeit(daily_mean_sql, con, runs=runs)
        d, t_run = timeit(daily_mean_running, path, runs=runs)
        ok = same(a, b) and same(a, c) and same(a, d)
        results[st] = (n, t_loops, t_pandas, t_load, t_query, t_run)
        print(f"  {st:>8}{n:>11,}{t_loops:>9.3f}{t_pandas:>9.3f}{t_load:>10.3f}{t_query:>10.3f}"
              f"{t_load + t_query:>10.3f}{t_run:>12.3f}  {ok}")

    # ------------------------------------------------------------ B3.3 profile
    print("\nB3.3 cProfile OF THE PLAIN-PYTHON VERSION (12 stations, 105,120 rows)")
    path12 = Path(tmp) / "year_12.csv"
    prof = cProfile.Profile()
    prof.runcall(daily_mean_loops, path12)
    buf = io.StringIO()
    stats = pstats.Stats(prof, stream=buf).sort_stats("tottime")
    stats.print_stats(6)
    lines = [l for l in buf.getvalue().splitlines() if l.strip()]
    start = next(i for i, l in enumerate(lines) if "tottime" in l)
    print("\n".join("  " + l for l in lines[start - 1:start + 7]))
    top = sorted(stats.stats.items(), key=lambda kv: -kv[1][2])[:1][0]
    print(f"  most time (own time): {top[0][2]} ({top[1][2]:.3f} s of {stats.total_tt:.3f} s)")
    cum = sorted(stats.stats.items(), key=lambda kv: -kv[1][3])
    sm = next(kv for kv in cum if kv[0][2] == "mean")
    print(f"  statistics.mean(): {sm[1][3]:.3f} s cumulative in {sm[1][1]:,} calls "
          f"({100 * sm[1][3] / stats.total_tt:.0f}% of the run)")
    # the finding, tested: replace statistics.mean by sum()/len()
    def loops_fast(path):
        groups = {}
        with open(path, newline="", encoding="utf-8") as f:
            for rec in csv.DictReader(f):
                groups.setdefault((rec["station"], rec["date"]), []).append(float(rec["pm25"]))
        return {k: sum(v) / len(v) for k, v in groups.items()}
    _, t_a = timeit(daily_mean_loops, path12, runs=3)
    fast, t_b = timeit(loops_fast, path12, runs=3)
    print(f"  after replacing statistics.mean by sum()/len(): {t_a:.3f} s -> {t_b:.3f} s "
          f"(same result: {same(fast, daily_mean_loops(path12))})")

    # ------------------------------------------------------------ memory (alternative concept)
    print("\nALTERNATIVE: store all readings then statistics.mean()  vs  running sum and count (12 stations)")
    for name, fn in (("store all values + mean", daily_mean_loops), ("running sum + count", daily_mean_running)):
        tracemalloc.start()
        fn(path12)
        peak = tracemalloc.get_traced_memory()[1] / 1e6
        tracemalloc.stop()
        print(f"  {name:<26} peak memory {peak:>7.1f} MB")


"""
B3.4 - ENGINEERING TRADE-OFF (based on the table above)
 * Differences observed. All methods grow about linearly with the rows (120 stations take 10-12x the
   time of 12). At 120 stations (1.05 million rows) pandas is about 5x faster than the plain
   loops (0.55 s against 2.70 s) because read_csv and groupby run in compiled code, but it
   loads the whole table into memory. SQL: the GROUP BY itself is fast (0.63 s), but loading the
   CSV into the database costs more than the query (2.36 s), so load + query (2.99 s) is no faster
   than the loops; the gain appears only after the data are loaded, because every further question
   costs just a query (and an index can make it cheaper still).
 * The profile shows where the loop version spends its time: reading and converting
   the CSV rows (csv DictReader, float) and statistics.mean(), which is slow because it is
   written for exact arithmetic with fractions; replacing it by sum()/len() gave a clear gain
   with the same results. Profile before optimising: the slow part is not always the loop.
 * One quick one-time analysis: pandas (a few lines, fastest to write and to run, the
   data is thrown away afterwards). If the file is small, plain loops are good enough and need
   no library.
 * A daily automated report: SQLite, because the data accumulate every day: load each new
   day once (executemany), keep the history, answer many different questions with
   SQL (GROUP BY, an index on (station, day)), and nothing has to be re-read from the CSV files. The
   report job then costs a query per day, not a re-scan of a year of CSV text.

ALTERNATIVE CONCEPT & COMPLEXITY - running sum and count in one pass
 - Storing all readings first, then calling statistics.mean(): time O(n) (every value is
   appended once and summed once) but a large constant; space O(n) - all n values are kept,
   although only stations x days means are needed.
 - Running sum + count in a dictionary: time O(n) with a smaller constant (no lists, no
   mean() call, see B3.2 column and the profile); space O(stations x days) - one [sum, count]
   per group, independent of how many readings each group has (see the peak-memory
   comparison). The price: it can only compute statistics that can be updated one value at a
   time (sum, count, min, max, mean); a median needs the stored values.
"""
