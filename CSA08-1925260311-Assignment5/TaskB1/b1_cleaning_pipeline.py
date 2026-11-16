"""
Task B1 - Implement and Validate the Cleaning Pipeline (7 marks)
  B1.1 validate the cleaning rules on a small file containing every problem of A1.1
  B1.2 compare with the Part A design          B1.3 store in SQLite and query
  B1.4 charts with interpretation              plus the given "Complete the Code" program
"""
import csv
import io
import os
import sys
import time
import tracemalloc
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import matplotlib
matplotlib.use("Agg")                                   # draw to files, no window needed
import matplotlib.pyplot as plt
import pandas as pd
from common import aqlib

# ======================================================= the given program (completed)
RAW = """station,date,pm25
Adyar,2026-10-01,48
Adyar,2026-10-02,NA
Adyar,2026-10-03,
Guindy,2026-10-01,95
Guindy,2026-10-02,-5
Guindy,2026-10-03,121
"""


def load_clean(text):
    """Returns (station, date, pm25) tuples for valid, non-negative readings only."""
    rows = []
    # TODO 1 (completed): read with csv.DictReader; skip rows whose pm25 is empty, 'NA' or
    # negative (and, as asked at the end of the task, above 999); convert pm25 to float
    for rec in csv.DictReader(io.StringIO(text)):
        value = rec["pm25"].strip()
        if value == "" or value.upper() == "NA":
            continue
        pm = float(value)
        if pm < 0 or pm > 999:
            continue
        rows.append((rec["station"], rec["date"], pm))
    return rows


def min_max(values):
    # TODO 2 (completed): scale each value to 0-1 using (v - min) / (max - min), rounded to 3 decimals
    lo, hi = min(values), max(values)
    return [round((v - lo) / (hi - lo), 3) for v in values]


clean = load_clean(RAW)
print(clean)
print(min_max([pm for _, _, pm in clean]))
# Expected output:
# [('Adyar', '2026-10-01', 48.0), ('Guindy', '2026-10-01', 95.0), ('Guindy', '2026-10-03', 121.0)]
# [0.0, 0.644, 1.0]

# the extra check for values above 999, with its test row
RAW_TEST = RAW + "Guindy,2026-10-04,5000\n"
print("test row 'Guindy,2026-10-04,5000' skipped:", load_clean(RAW_TEST) == clean)


# ============================================================ B1.1 validation
def make_problem_file():
    """A small file that contains EVERY problem listed in A1.1."""
    rows = [
        ["Adyar", "2026-10-01", "0", "48.0", "70.0", "30.0", "27.0"],
        ["Adyar", "2026-10-01", "1", "", "72.0", "31.0", "26.5"],        # blank
        ["Adyar", "2026-10-01", "2", "NA", "74.0", "29.0", "26.0"],      # NA  (filled from hour 0)
        ["Adyar", "2026-10-01", "3", "-5.0", "75.0", "28.0", "25.5"],    # negative
        ["Adyar", "2026-10-01", "4", "9999", "76.0", "27.0", "25.0"],    # impossibly large
        ["Adyar", "2026-10-01", "5", "9999", "77.0", "27.0", "25.0"],    # still within the gap limit?
        ["Adyar", "2026-10-01", "6", "9999", "78.0", "27.0", "25.0"],    # gap longer than 3 -> stays empty
        ["Adyar", "2026-10-01", "7", "50.0", "80.0", "26.0", "25.0"],
        ["Adyar", "2026-10-01", "7", "50.0", "80.0", "26.0", "25.0"],    # duplicate row
        [" GUINDY ", "01/10/2026", "0", "95.0", "150.0", "40.0", "28.0"],  # untidy name, DD/MM/YYYY
        ["Guindy", "2026-10-01", "1", "96.0", "152.0", "41.0", "28.5"],
        ["Manali", "2026-10-01", "0", "60.0", "100.0", "35.0", "82.4"],  # Fahrenheit station
        ["Manali", "2026-10-01", "1", "61.0", "101.0", "36.0", "83.3"],
        ["Manali", "2026-10-01", "2"],                                    # damaged: 3 fields
    ]
    return rows


def show(rows, title):
    print(f"\n{title}")
    for r in rows:
        print("  ", r)


def run_b11():
    raw = make_problem_file()
    show(raw, "B1.1 DATA BEFORE CLEANING (14 rows)")
    cleaned, rep = aqlib.clean_rows(raw)
    show(cleaned, f"DATA AFTER CLEANING ({len(cleaned)} rows)  columns: station, date, hour, pm25, pm10, no2, temp_c")
    print("\nCleaning report:", rep)
    # automatic checks that every rule worked
    checks = {
        "duplicate row removed": rep["duplicates"] == 1,
        "damaged row (3 fields) rejected": rep["rejected_rows"] == 1,
        "station name tidied (' GUINDY ' -> 'Guindy')": all(r[0] in ("Adyar", "Guindy", "Manali") for r in cleaned),
        "DD/MM/YYYY converted to ISO": all(r[1] == "2026-10-01" for r in cleaned),
        "Fahrenheit station converted (82.4 F -> 28.0 C)": [r[6] for r in cleaned if r[0] == "Manali"][0] == 28.0,
        "negative and 9999 values detected": rep["impossible"] >= 4,
        "NA/blank filled from previous hour (Adyar hour 2 = 48.0)": [r[3] for r in cleaned if r[0] == "Adyar" and r[2] == 2][0] == 48.0,
        "gap longer than 3 hours left empty (hour 6 None)": [r[3] for r in cleaned if r[0] == "Adyar" and r[2] == 6][0] is None,
    }
    for name, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    return cleaned, rep


# ============================================================ B1.3 / B1.4
def run_store_and_query(workdir):
    raw = aqlib.generate_rows(12, 31, seed=11)                     # October, 12 stations
    cleaned, rep = aqlib.clean_rows(raw)
    print(f"\nOctober data: {len(raw):,} raw rows -> {len(cleaned):,} clean rows; report: {rep}")
    aqlib.write_csv(raw, workdir / "october_raw.csv")
    con = aqlib.build_db(cleaned, str(workdir / "airquality.db") if False else ":memory:",
                         fahrenheit=rep["fahrenheit_stations"])
    print("\nB1.3 SQL answers (executemany load):")
    q1 = con.execute("SELECT ROUND(AVG(r.pm25), 2) FROM readings r JOIN stations s USING(station_id) "
                     "WHERE s.name = ? AND r.day BETWEEN '2026-10-01' AND '2026-10-31'", ("Adyar",)).fetchone()[0]
    print(f"  Q1 average PM2.5 of Adyar in October            : {q1}")
    q2 = con.execute("SELECT s.name, ROUND(AVG(r.pm25), 2) a FROM readings r JOIN stations s USING(station_id) "
                     "GROUP BY s.name ORDER BY a DESC LIMIT 3").fetchall()
    print(f"  Q2 three most polluted stations (mean PM2.5)    : {q2}")
    q3 = con.execute("SELECT hour, ROUND(AVG(pm25), 1) a FROM readings GROUP BY hour ORDER BY a DESC LIMIT 3").fetchall()
    print(f"  Q3 three worst hours of the day (city-wide)     : {q3}")
    # cross-check Q1 with plain Python on the cleaned data
    vals = [r[3] for r in cleaned if r[0] == "Adyar" and r[3] is not None]
    print(f"  cross-check Q1 with Python: {round(sum(vals) / len(vals), 2)}  (same: {round(sum(vals) / len(vals), 2) == q1})")
    return con, cleaned, q2, q3


def run_charts(con, workdir):
    out = workdir / "charts"
    out.mkdir(exist_ok=True)
    df = pd.read_sql_query(
        "SELECT s.name station, r.day, r.hour, r.pm25, r.temp_c FROM readings r "
        "JOIN stations s USING(station_id)", con)
    notes = []

    # 1. line: daily trend of one station over the month
    daily = df[df.station == "Adyar"].groupby("day").pm25.mean()
    fig, ax = plt.subplots(figsize=(8, 3.6))
    ax.plot(range(1, len(daily) + 1), daily.values, marker="o", ms=3)
    ax.set_xlabel("Day of October 2026"); ax.set_ylabel("Daily mean PM2.5 (ug/m3)")
    ax.set_title("Adyar: daily mean PM2.5 in October"); ax.grid(alpha=.3)
    fig.tight_layout(); fig.savefig(out / "1_trend_adyar.png", dpi=110); plt.close(fig)
    hi_day = int(daily.values.argmax()) + 1
    change = daily.values[-7:].mean() - daily.values[:7].mean()
    trend = ("rises" if change > 3 else "falls" if change < -3 else "shows no clear rise or fall")
    notes.append(("1_trend_adyar.png (line)",
                  f"The daily mean stays between {daily.min():.1f} and {daily.max():.1f} ug/m3 with its peak on "
                  f"day {hi_day}; the last week's mean differs from the first week's by {change:+.1f}, so the month "
                  f"{trend} overall. A line chart is the right choice because the x-axis is ordered time."))

    # 2. bar: stations compared
    means = df.groupby("station").pm25.mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(means.index, means.values)
    ax.set_xlabel("Mean PM2.5 (ug/m3)"); ax.set_ylabel("Station"); ax.set_title("Mean PM2.5 by station, October")
    fig.tight_layout(); fig.savefig(out / "2_stations_bar.png", dpi=110); plt.close(fig)
    notes.append(("2_stations_bar.png (bar)",
                  f"{means.index[-1]} is the most polluted station ({means.iloc[-1]:.1f}) and {means.index[0]} "
                  f"the cleanest ({means.iloc[0]:.1f}); the {means.iloc[-1] / means.iloc[0]:.1f}x difference shows "
                  f"that stations must be compared separately and not averaged into one city number."))

    # 3. scatter: temperature vs PM2.5
    sample = df.dropna(subset=["pm25", "temp_c"]).sample(1500, random_state=1)
    r = df[["pm25", "temp_c"]].corr().iloc[0, 1]
    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.scatter(sample.temp_c, sample.pm25, s=6, alpha=.4)
    ax.set_xlabel("Temperature (degC)"); ax.set_ylabel("PM2.5 (ug/m3)")
    ax.set_title(f"Temperature vs PM2.5 (1,500 readings, r = {r:.2f})")
    fig.tight_layout(); fig.savefig(out / "3_temp_scatter.png", dpi=110); plt.close(fig)
    notes.append(("3_temp_scatter.png (scatter)",
                  f"The correlation coefficient is r = {r:.2f}, i.e. a {'weak' if abs(r) < 0.3 else 'moderate' if abs(r) < 0.6 else 'strong'} relationship in this data set. "
                  f"A scatter plot shows the whole cloud, so a weak link is visible at once; correlation "
                  f"alone would not prove that temperature causes pollution."))

    # 4. histogram: distribution of PM2.5
    fig, ax = plt.subplots(figsize=(6.5, 4))
    ax.hist(df.pm25.dropna(), bins=30)
    ax.axvline(df.pm25.mean(), color="red", ls="--", label=f"mean {df.pm25.mean():.1f}")
    ax.set_xlabel("PM2.5 (ug/m3)"); ax.set_ylabel("Number of readings"); ax.set_title("Distribution of PM2.5")
    ax.legend(); fig.tight_layout(); fig.savefig(out / "4_hist_pm25.png", dpi=110); plt.close(fig)
    skew = df.pm25.skew()
    shape = ("right-skewed (a tail of a few very polluted hours)" if skew > 0.5 else
             "left-skewed" if skew < -0.5 else "roughly symmetric (bell-shaped)")
    notes.append(("4_hist_pm25.png (histogram)",
                  f"Most readings lie between {df.pm25.quantile(.1):.0f} and {df.pm25.quantile(.9):.0f} ug/m3; the "
                  f"distribution is {shape} (skewness {skew:.2f}), and the mean ({df.pm25.mean():.1f}) is close to the "
                  f"median ({df.pm25.median():.1f}). A histogram shows the shape of the data, which a single "
                  f"average cannot."))

    # 5. box plot by hour: hours with worst air
    groups = [df[df.hour == h].pm25.dropna().values for h in range(24)]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.boxplot(groups, tick_labels=[str(h) for h in range(24)], showfliers=False)
    ax.set_xlabel("Hour of the day"); ax.set_ylabel("PM2.5 (ug/m3)"); ax.set_title("PM2.5 by hour of the day")
    fig.tight_layout(); fig.savefig(out / "5_box_by_hour.png", dpi=110); plt.close(fig)
    hourly = df.groupby("hour").pm25.mean()
    notes.append(("5_box_by_hour.png (box plot)",
                  f"The worst hour is {int(hourly.idxmax())}:00 (mean {hourly.max():.1f}) and the best is "
                  f"{int(hourly.idxmin())}:00 ({hourly.min():.1f}); the morning peak is at {int(hourly[5:12].idxmax())}:00 "
                  f"({hourly[5:12].max():.1f}) and the evening peak at {int(hourly[16:23].idxmax())}:00 "
                  f"({hourly[16:23].max():.1f}). The boxes show the spread inside each hour, which a bar of means would hide."))
    print("\nB1.4 charts saved in", out.name + "/ with interpretations:")
    for name, text in notes:
        print(f"  * {name}: {text}")


# ================================================ alternative: pandas pipeline
def clean_pandas(raw_rows):
    df = pd.DataFrame(raw_rows, columns=aqlib.HEADER)
    df["station"] = df.station.str.split().str.join(" ").str.title()
    iso = pd.to_datetime(df.date.str.strip(), format="%Y-%m-%d", errors="coerce")
    alt = pd.to_datetime(df.date.str.strip(), format="%d/%m/%Y", errors="coerce")
    df["date"] = iso.fillna(alt).dt.strftime("%Y-%m-%d")
    for c in ("pm25", "pm10", "no2", "temp"):
        df[c] = pd.to_numeric(df[c].replace({"NA": None, "": None}), errors="coerce")
    df["hour"] = df.hour.astype(int)
    df = df.drop_duplicates(["station", "date", "hour"])
    for c in ("pm25", "pm10", "no2"):
        df.loc[(df[c] < 0) | (df[c] > aqlib.PM_MAX), c] = float("nan")
    fahr = df.groupby("station").temp.transform("median") > 45
    df.loc[fahr, "temp"] = ((df.loc[fahr, "temp"] - 32) * 5 / 9).round(1)
    df = df.sort_values(["station", "date", "hour"])
    df[["pm25", "pm10", "no2"]] = df.groupby("station")[["pm25", "pm10", "no2"]].ffill(limit=3)
    return df


def compare_pandas():
    print("\nALTERNATIVE: pandas pipeline vs csv-module loops (time: one run, no tracing; "
          "peak memory: separate tracemalloc run, only up to 100,000 rows)")
    print(f"  {'rows':>10}{'loops s':>10}{'pandas s':>10}{'speed-up':>10}{'loops MB':>10}{'pandas MB':>11}{'rows out (loops/pandas)':>26}")
    for n_st, n_days in ((1, 42), (12, 347), (12, 3472)):
        raw = aqlib.generate_rows(n_st, n_days, seed=3)
        t0 = time.perf_counter(); out1, _ = aqlib.clean_rows(raw); t1 = time.perf_counter() - t0
        t0 = time.perf_counter(); out2 = clean_pandas(raw); t2 = time.perf_counter() - t0
        if len(raw) <= 120_000:
            tracemalloc.start(); aqlib.clean_rows(raw); m1 = tracemalloc.get_traced_memory()[1] / 1e6; tracemalloc.stop()
            tracemalloc.start(); clean_pandas(raw); m2 = tracemalloc.get_traced_memory()[1] / 1e6; tracemalloc.stop()
            mem = f"{m1:>10.1f}{m2:>11.1f}"
        else:
            mem = f"{'~10x':>10}{'~10x':>11}"                 # memory grows linearly with the rows
        print(f"  {len(raw):>10,}{t1:>10.3f}{t2:>10.3f}{t1 / t2:>9.1f}x{mem}{f'{len(out1):,} / {len(out2):,}':>26}")


if __name__ == "__main__":
    cleaned, rep = run_b11()
    work = HERE / "output"
    work.mkdir(exist_ok=True)
    con, _, _, _ = run_store_and_query(work)
    run_charts(con, work)
    compare_pandas()


"""
B1.2 - COMPARISON WITH THE PART A DESIGN
 Same as designed: missing / NA / blank -> empty then forward fill of at most 3 hours;
   negative or > 999 -> impossible (treated as missing); duplicate (station, date, hour)
   keeps the FIRST row; Fahrenheit stations found by median temperature > 45 and converted;
   ISO dates, tidy station names; clean data stored with executemany.
 Changes made while coding (and why):
   1. Rows with the wrong number of fields (damaged lines) are REJECTED and counted -
      A2 only listed them; a real file contained them.
   2. DD/MM/YYYY dates are accepted and converted instead of being rejected - found in test data.
   3. The 999 limit was applied to pm10 and no2 as well, not only PM2.5, to keep one rule.
   4. The forward fill uses the last REAL value, so a filled value never extends the gap limit
      (first version let a filled value restart the 3-hour counter; the test row for hour 6 caught it).

ALTERNATIVE CONCEPT & COMPLEXITY - pandas instead of csv + loops
 - Both are O(n) in the number of rows (read, convert, drop duplicates with a hash, one
   forward fill). pandas does the per-row work in compiled code, so its constant is much
   smaller for large inputs: see the table (about 2x faster at 100,000 and 1,000,000 rows, but SLOWER at
   1,000 rows because of pandas' fixed start-up cost). Memory: the loops hold a Python
   object for every value (float, string, tuple), pandas holds typed columns (8 bytes per float), so in
   the measurement pandas used about half the peak memory of the loops, and both grow linearly with n
   (space O(n)). The csv + loops version needs no extra library and can STREAM line by line
   (O(1) memory for the reading itself, which pandas read_csv can only do with chunksize).
"""
