"""
Task B2 - Engineer Adversarial Data (5 marks)
  1. files with a missing column, a wrong delimiter, another encoding and an empty file
  2. SQL built with + versus a ? placeholder (a name containing a quote, and an injection attempt)
  3. the sentiment scorer on sarcasm, double negatives and mixed opinions
  4. what each adversarial input reveals about the design
plus the given "Complete the Code" program (sqlite3, executemany, parameterised SELECT).
"""
import csv
import io
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import ai_app

# ==================================================== the given program (completed)
readings = [("Adyar", "2026-10-01", 48.0), ("Guindy", "2026-10-01", 95.0),
            ("Guindy", "2026-10-03", 121.0), ("Adyar", "2026-10-04", 60.0)]

con = sqlite3.connect(":memory:")
con.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
# TODO 1 (completed): insert all readings with ONE executemany call using ? placeholders, then commit
con.executemany("INSERT INTO aq (station, day, pm25) VALUES (?, ?, ?)", readings)
con.commit()


def station_average(name):
    # TODO 2 (completed): average pm25 of the given station using a parameterised SELECT ... WHERE station = ?
    return con.execute("SELECT AVG(pm25) FROM aq WHERE station = ?", (name,)).fetchone()[0]


print(station_average("Adyar"), station_average("Guindy"))
print(station_average("Adyar' OR '1'='1"))        # an injection attempt finds nothing
# Expected output:
# 54.0 108.0
# None
# WHY None: the ? placeholder passes the whole text as ONE VALUE. The database looks for a station
# whose name is literally  Adyar' OR '1'='1  - there is none, so no row matches, and AVG() of zero
# rows is NULL, which Python returns as None. The quote characters are data, never SQL syntax,
# so the attacker cannot change the structure of the query (and cannot see all rows).


# ============================================================ 1. adversarial files
REQUIRED = ["station", "date", "pm25"]


def naive_load(path):
    """The first, careless loader: utf-8, comma, trusts the header."""
    with open(path, newline="", encoding="utf-8") as f:
        return [(r["station"], r["date"], float(r["pm25"])) for r in csv.DictReader(f)]


def load_station_csv(path):
    """Robust loader. Returns (rows, problems); never raises for a bad FILE."""
    problems = []
    try:
        data = Path(path).read_bytes()
    except OSError as e:
        return [], [f"cannot read file: {e}"]
    if not data.strip():
        return [], ["file is empty (no header, no rows)"]
    # encoding: BOM-aware utf-8, utf-16 with BOM, otherwise fall back to cp1252 and say so
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        text, enc = data.decode("utf-16"), "utf-16"
    else:
        try:
            text, enc = data.decode("utf-8-sig"), "utf-8"
        except UnicodeDecodeError:
            text, enc = data.decode("cp1252", errors="replace"), "cp1252 (guessed)"
            problems.append("not valid UTF-8: decoded as cp1252, please check the characters")
    # delimiter: the one for which the header contains the required column names
    header_line = text.splitlines()[0]
    delim = next((d for d in (",", ";", "\t", "|") if set(REQUIRED) <= {h.strip().lower() for h in header_line.split(d)}), None)
    if delim is None:
        delim = max((",", ";", "\t", "|"), key=header_line.count)
    elif delim != ",":
        problems.append(f"delimiter {delim!r} detected instead of ','")
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    header = [h.strip().lower() for h in (reader.fieldnames or [])]
    missing = [c for c in REQUIRED if c not in header]
    if missing:
        return [], problems + [f"missing required column(s): {', '.join(missing)} (found: {header})"]
    rows = []
    for n, rec in enumerate(reader, start=2):
        rec = {k.strip().lower(): (v or "").strip() for k, v in rec.items() if k}
        try:
            rows.append((rec["station"], rec["date"], float(rec["pm25"])))
        except ValueError:
            problems.append(f"line {n}: pm25 {rec['pm25']!r} is not a number - skipped")
    return rows, problems


ADVERSARIAL = {
    "missing_column.csv": b"station,date\nAdyar,2026-10-01\n",
    "wrong_delimiter.csv": b"station;date;pm25\nAdyar;2026-10-01;48\nGuindy;2026-10-01;95\n",
    "latin1_encoding.csv": "station,date,pm25\nCaf\xe9 Road,2026-10-01,48\n".encode("latin-1"),
    "utf16_encoding.csv": "station,date,pm25\nAdyar,2026-10-01,48\n".encode("utf-16"),
    "empty.csv": b"",
}


def run_files(folder):
    folder.mkdir(exist_ok=True)
    print("\n1. ADVERSARIAL FILES   (before = naive loader, after = robust loader)")
    for name, content in ADVERSARIAL.items():
        p = folder / name
        p.write_bytes(content)
        try:
            before = naive_load(p)
        except Exception as e:                                    # show what the naive loader does
            before = f"{type(e).__name__}: {e}"
        rows, problems = load_station_csv(p)
        print(f"  {name}\n     before: {before}\n     after : rows={rows} problems={problems}")


# ===================================================== 2. quote character / injection
def average_by_concat(name):
    """UNSAFE: the SQL text is built by joining strings."""
    sql = "SELECT AVG(pm25) FROM aq WHERE station = '" + name + "'"
    return con.execute(sql).fetchone()[0], sql


def run_sql():
    con.execute("INSERT INTO aq VALUES (?, ?, ?)", ("O'Brien Road", "2026-10-01", 70.0))
    print("\n2. STATION NAME WITH A QUOTE: SQL built with + versus a ? placeholder")
    for name in ("O'Brien Road", "Adyar' OR '1'='1", "x'; DROP TABLE aq; --"):
        print(f"  input {name!r}")
        try:
            value, sql = average_by_concat(name)
            print(f"     with +      : {value}   SQL was: {sql}")
        except (sqlite3.OperationalError, sqlite3.ProgrammingError) as e:
            print(f"     with +      : {type(e).__name__}: {e}   SQL was: SELECT ... station = '{name}'")
        print(f"     with ?      : {station_average(name)}")
    print("  table still exists after the DROP attempt:",
          con.execute("SELECT COUNT(*) FROM aq").fetchone()[0], "rows")
    print("  (sqlite3.execute() refuses a second statement; con.executescript(sql) would have run the DROP.)")


# ========================================================= 3. sentiment adversarial
CASES = [
    # (text, what a human reads, type of trick)
    ("Great, another broken road. So helpful.", "negative", "sarcasm"),
    ("The helpline was so helpful, I waited two hours.", "negative", "sarcasm"),
    ("The staff were never not helpful.", "positive", "double negative"),
    ("It is not that the service is not good.", "positive", "double negative"),
    ("The roads are clean but the bus is slow and rude.", "mixed", "mixed opinion"),
    ("Clean roads and fast buses, but the smoke is terrible.", "negative", "mixed / unknown word"),
    ("The metro is not very good.", "negative", "negator not adjacent"),
    ("No smoke today, the air is clean.", "positive", "negation that works"),
]


def run_sentiment():
    print("\n3. SENTIMENT SCORER ON ADVERSARIAL SENTENCES")
    wrong = 0
    print(f"  {'trick':<24}{'human':<10}{'scorer':<10}{'score':>6}  text")
    for text, human, kind in CASES:
        got = ai_app.label(text)
        ok = (got == human)
        wrong += not ok
        print(f"  {kind:<24}{human:<10}{got:<10}{ai_app.score(text):>6}  {'OK ' if ok else 'FAIL'} {text}")
    print(f"  failed on {wrong} of {len(CASES)} sentences")


# ================================================= alternative: executemany vs execute loop
def run_insert_timing():
    print("\nALTERNATIVE: executemany() versus execute() in a loop (in-memory database, one commit at the end)")
    print(f"  {'rows':>9}{'executemany s':>15}{'execute loop s':>16}{'ratio':>8}")
    for n in (1_000, 10_000, 100_000):
        data = [("S%03d" % (i % 120), "2026-10-01", float(i % 100)) for i in range(n)]
        c1 = sqlite3.connect(":memory:"); c1.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
        t0 = time.perf_counter(); c1.executemany("INSERT INTO aq VALUES (?, ?, ?)", data); c1.commit()
        t1 = time.perf_counter() - t0
        c2 = sqlite3.connect(":memory:"); c2.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
        t0 = time.perf_counter()
        for row in data:
            c2.execute("INSERT INTO aq VALUES (?, ?, ?)", row)
        c2.commit()
        t2 = time.perf_counter() - t0
        print(f"  {n:>9,}{t1:>15.4f}{t2:>16.4f}{t2 / t1:>7.1f}x")
    # a commit after EVERY row on a disk file is the real danger
    path = HERE / "output_commit_test.db"
    path.unlink(missing_ok=True)
    c3 = sqlite3.connect(path); c3.execute("CREATE TABLE aq (station TEXT, day TEXT, pm25 REAL)")
    t0 = time.perf_counter()
    for i in range(300):
        c3.execute("INSERT INTO aq VALUES (?, ?, ?)", ("S", "2026-10-01", float(i))); c3.commit()
    t3 = time.perf_counter() - t0
    c3.close(); path.unlink(missing_ok=True)
    print(f"  300 rows with a commit after EACH row on a disk file: {t3:.3f} s "
          f"({t3 / 300 * 1000:.2f} ms per row) - the commit (disk sync) dominates, so batch the commit.")


if __name__ == "__main__":
    run_files(HERE / "adversarial_files")
    run_sql()
    run_sentiment()
    run_insert_timing()


"""
4. WHAT EACH ADVERSARIAL INPUT REVEALS ABOUT THE DESIGN
 - Missing column: the first loader assumed the header; it crashed with a KeyError that says
   nothing about the real problem. A loader must VALIDATE the header (required columns) and
   report which are missing - the design needs a data contract, not trust.
 - Wrong delimiter: the file is read as ONE column; the naive loader crashes at the first
   row. Delimiter should be detected from the header (or configured), and the choice logged.
 - Other encoding: utf-8 is an assumption; a latin-1/cp1252 byte raises UnicodeDecodeError, a utf-16
   file looks like garbage. The reader must state its encoding, try the likely ones and warn
   when it had to guess (a guessed accent can silently change a station name).
 - Empty file: no header at all; without a check the program either crashes or reports
   "0 rows" as if all was well. Empty is different from "no valid rows" and must be named.
 - Quote in a station name: building SQL with + makes the DATA part of the CODE: a legitimate
   O'Brien Road breaks the query (syntax error), and a hostile name (' OR '1'='1) changes its
   meaning and returns every station's data (here the average of ALL 5 rows, 78.8, instead of None).
   The ? placeholder keeps data and code separate - always use it for any value that comes from
   outside the program.
 - Sentiment failures: the lexicon scorer has no notion of tone, context or word order beyond
   the previous word. Sarcasm (positive words used negatively), double negatives (only a
   single flip), a negator that is not adjacent ("not very good"), mixed opinions (it must
   output ONE label) and words missing from the list ("terrible") all expose the same design
   limit: it counts words; it does not understand sentences. Its output should therefore be
   used for trends over many complaints, not for judging one complaint.

ALTERNATIVE CONCEPT & COMPLEXITY - string-joined SQL, and execute() in a loop
 - If the SQL is built by joining strings, f"SELECT ... WHERE station = '{name}'":
   with the input  Adyar' OR '1'='1  the text becomes  ... WHERE station = 'Adyar' OR '1'='1'
   and the condition is TRUE for EVERY row, so the query returns the average of ALL stations
   (78.8 here, the mean of all 5 rows) - a wrong answer and a data leak (with SELECT * it would list every row).
   Time and space are the same as the safe version; the difference is correctness and
   security, and the string version has to be re-parsed (re-compiled) for every different value.
 - executemany() versus execute() in a loop for n rows: both are O(n) in time and O(1)
   extra space (rows can come from a generator), but executemany does the looping inside the
   sqlite3 module and avoids n separate Python calls (the module caches the compiled statement in
   both cases), so it is faster by a constant factor of about 2 (table above); and one
   commit for all rows avoids n disk syncs (the last measurement).
"""
