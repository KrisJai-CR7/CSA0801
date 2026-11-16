"""
common/aqlib.py - shared helpers for the City Air-Quality case study.
  * generate_rows()  : synthetic station files with every data-quality problem of A1.1
  * clean_rows()     : the cleaning rules designed in A2 (plain Python, csv-module style)
  * build_db()       : the SQLite design of A1.2 (stations + readings)
"""
import math
import random
import sqlite3
import statistics
from datetime import date, datetime, timedelta

NAMES = ["Adyar", "Guindy", "T Nagar", "Velachery", "Anna Nagar", "Kilpauk", "Manali",
         "Perungudi", "Alandur", "Royapuram", "Besant Nagar", "Ambattur"]
FAHRENHEIT = {"Manali", "Ambattur"}              # the two stations that report in Fahrenheit
HEADER = ["station", "date", "hour", "pm25", "pm10", "no2", "temp"]

PM_MAX = 999            # larger readings are sensor faults
TEMP_MIN, TEMP_MAX = -10.0, 60.0                  # plausible air temperature, Celsius
FFILL_LIMIT = 3         # forward-fill at most 3 consecutive missing hours


def station_names(n):
    return NAMES[:n] if n <= 12 else NAMES + [f"Station {i:03d}" for i in range(13, n + 1)]


# ------------------------------------------------------------- data generator
def generate_rows(n_stations, days, seed=0, dirty=True, start=date(2026, 10, 1)):
    """Raw CSV rows (lists of strings). dirty=True injects the problems of A1.1."""
    rnd = random.Random(seed)
    rows = []
    for si, name in enumerate(station_names(n_stations)):
        base = 40 + (si * 7) % 50
        fahr = name in FAHRENHEIT
        for d in range(days):
            day = (start + timedelta(days=d)).isoformat()
            for h in range(24):
                peak = 25 * math.exp(-((h - 8) ** 2) / 18) + 30 * math.exp(-((h - 20) ** 2) / 18)
                pm25 = max(1.0, base + peak + rnd.gauss(0, 8))
                pm10 = pm25 * 1.6 + rnd.gauss(0, 6)
                no2 = 20 + peak * 0.8 + rnd.gauss(0, 4)
                temp = 27 + 6 * math.sin((h - 9) / 24 * 2 * math.pi) + rnd.gauss(0, 1)
                if fahr:
                    temp = temp * 9 / 5 + 32
                row = [name, day, str(h), f"{pm25:.1f}", f"{pm10:.1f}", f"{no2:.1f}", f"{temp:.1f}"]
                if dirty:
                    r = rnd.random()
                    if r < 0.015:
                        row[3] = ""                       # blank
                    elif r < 0.025:
                        row[3] = "NA"                     # NA
                    elif r < 0.030:
                        row[3] = f"-{rnd.randint(1, 20)}.0"   # negative
                    elif r < 0.033:
                        row[3] = "9999"                   # impossibly large
                    if rnd.random() < 0.01:
                        row[4] = ""
                    r = rnd.random()
                    if r < 0.006:
                        row[0] = " " + name.upper() + " "   # untidy station name
                    elif r < 0.010:
                        row[1] = f"{day[8:]}/{day[5:7]}/{day[:4]}"   # DD/MM/YYYY
                rows.append(row)
                if dirty and rnd.random() < 0.01:
                    rows.append(list(row))                # duplicate row
    return rows


def write_csv(rows, path, header=HEADER):
    import csv
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


# ---------------------------------------------------------------- cleaning rules
def parse_number(text, lo, hi):
    """-> (value or None, kind) where kind is 'ok', 'missing' or 'impossible'."""
    s = (text or "").strip()
    if s == "" or s.upper() in ("NA", "N/A", "NAN", "NULL"):
        return None, "missing"
    try:
        v = float(s)
    except ValueError:
        return None, "missing"
    if v < lo or v > hi:
        return None, "impossible"
    return v, "ok"


def parse_date(text):
    s = text.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def clean_rows(raw_rows):
    """Apply the rules of A2.1. Returns (clean_rows, report).
    clean row = (station, date, hour, pm25, pm10, no2, temp_c); a value may be None."""
    rep = dict(rows_in=0, rejected_rows=0, duplicates=0, missing=0, impossible=0,
               name_fixed=0, date_fixed=0, fahrenheit_stations=[], filled=0)
    seen, parsed = set(), []
    for row in raw_rows:
        rep["rows_in"] += 1
        if len(row) != 7:
            rep["rejected_rows"] += 1
            continue
        raw_name = row[0]
        name = " ".join(raw_name.split()).title()
        if name != raw_name:
            rep["name_fixed"] += 1
        day = parse_date(row[1])
        try:
            hour = int(row[2])
        except ValueError:
            hour = -1
        if not name or day is None or not 0 <= hour <= 23:
            rep["rejected_rows"] += 1
            continue
        if day != row[1].strip():
            rep["date_fixed"] += 1
        key = (name, day, hour)
        if key in seen:                                   # duplicate: keep the first
            rep["duplicates"] += 1
            continue
        seen.add(key)
        vals = []
        for text, hi in ((row[3], PM_MAX), (row[4], PM_MAX), (row[5], PM_MAX)):
            v, kind = parse_number(text, 0, hi)
            if kind != "ok":
                rep[kind] += 1
            vals.append(v)
        t, _ = parse_number(row[6], -50, 200)          # wide range first; unit decided below
        parsed.append([name, day, hour, vals[0], vals[1], vals[2], t])

    # Fahrenheit stations: median valid temperature of a station above 45
    temps = {}
    for p in parsed:
        if p[6] is not None:
            temps.setdefault(p[0], []).append(p[6])
    fahr = {s for s, v in temps.items() if statistics.median(v) > 45}
    rep["fahrenheit_stations"] = sorted(fahr)
    for p in parsed:
        if p[6] is not None:
            if p[0] in fahr:
                p[6] = round((p[6] - 32) * 5 / 9, 1)
            if not TEMP_MIN <= p[6] <= TEMP_MAX:
                rep["impossible"] += 1
                p[6] = None

    # forward fill of short gaps: previous value of the SAME station, at most 3 hours
    parsed.sort(key=lambda p: (p[0], p[1], p[2]))
    last = {}                                             # (station, column) -> (index, value)
    for i, p in enumerate(parsed):
        for c in (3, 4, 5):
            if p[c] is None:
                prev = last.get((p[0], c))
                if prev is not None and i - prev[0] <= FFILL_LIMIT and prev[2] == p[0]:
                    p[c] = prev[1]                         # the 'last' entry stays the last REAL
                    rep["filled"] += 1                     # value, so at most 3 hours are filled
                    continue
            else:
                last[(p[0], c)] = (i, p[c], p[0])
    return [tuple(p) for p in parsed], rep


# ---------------------------------------------------------------- SQLite design (A1.2)
SCHEMA = """
CREATE TABLE stations (
    station_id INTEGER PRIMARY KEY,
    name       TEXT NOT NULL UNIQUE,
    reports_fahrenheit INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE readings (
    reading_id INTEGER PRIMARY KEY,
    station_id INTEGER NOT NULL REFERENCES stations(station_id),
    day        TEXT NOT NULL,             -- ISO date YYYY-MM-DD
    hour       INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
    pm25 REAL, pm10 REAL, no2 REAL, temp_c REAL
);
"""


def build_db(clean, path=":memory:", fahrenheit=()):
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    names = sorted({r[0] for r in clean})
    con.executemany("INSERT INTO stations(name, reports_fahrenheit) VALUES (?, ?)",
                    [(n, int(n in fahrenheit)) for n in names])
    ids = dict(con.execute("SELECT name, station_id FROM stations"))
    con.executemany(
        "INSERT INTO readings(station_id, day, hour, pm25, pm10, no2, temp_c) VALUES (?,?,?,?,?,?,?)",
        ((ids[r[0]], r[1], r[2], r[3], r[4], r[5], r[6]) for r in clean))
    con.commit()
    return con
