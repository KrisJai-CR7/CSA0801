"""
Task 1 - File-Processing Design Review: Diagnose and Repair a Poor Script (6 marks)

ORIGINAL (poor) script - kept here only as text, it is NOT run:

    f = open("C:\\\\Users\\\\Office\\\\Desktop\\\\mess_oct.txt")
    data = f.read()
    total = 0
    report = ""
    for line in data.split("\\n"):
        try:
            parts = line.split(",")
            total = total + int(parts[2])
            report = report + parts[1] + " " + parts[2] + "\\n"
        except:
            pass
    print(report)
    print("Total", total)
"""
import os
import sys
import tempfile
import time
import tracemalloc
from decimal import Decimal, InvalidOperation


# ------------------------------------------------ Task 1.1 - the diagnosis
DEFICIENCIES = [
    ("Hard-coded absolute path",
     "Works only on one computer (C:\\Users\\Office\\...); the script fails for every other user "
     "or when the file is renamed/moved or the next month's file (mess_nov.txt) is needed."),
    ("File never closed (no with statement)",
     "The handle stays open: on Windows the file stays locked so the office cannot edit/"
     "replace it; many runs leak handles; buffered data/OS resources are freed only by luck."),
    ("Whole file read into memory (f.read())",
     "Memory grows with the file: 50,000 lines are read AND copied by split(); a "
     "much bigger file may exhaust memory. Line-by-line iteration needs one line."),
    ("Bare except with pass",
     "Swallows EVERY error silently: bad lines, typing mistakes (a NameError) and even "
     "KeyboardInterrupt. The office never learns that a bill was skipped; the total is "
     "silently too low."),
    ("int() on amounts with paise (1250.50)",
     "int('1250.50') raises ValueError, so every bill with paise is thrown away "
     "by the bare except. Using float would add rounding errors; money needs Decimal."),
    ("Report built with repeated +",
     "report = report + ... creates a new string every time (up to O(n^2) copying for "
     "50,000 lines). A list plus ''.join() is O(n)."),
    ("Empty last line of the file",
     "split('\\n') yields '' after the final newline; it raises IndexError that the bare "
     "except hides - the empty line is treated like a real error and nobody can tell "
     "the difference between 'harmless blank' and 'damaged'."),
    ("No record of rejected lines",
     "Nothing says WHICH lines were rejected or why, so wrong totals cannot be traced "
     "or corrected, and students may be under/over-charged without anyone noticing."),
]


def print_diagnosis():
    print("TASK 1.1  DESIGN DEFICIENCIES (8 found) and what could go wrong")
    for i, (title, risk) in enumerate(DEFICIENCIES, 1):
        print(f"  {i}. {title}\n       -> {risk}")


# ------------------------------------------------- Task 1.2 - the repair
def total_bills(file_name):
    """
    Total the mess bills in `file_name` (one line per student:
    register number, name, amount).
    Returns (total as Decimal, report lines, rejected) where
    rejected = [(line_number, line_text, reason), ...].
    """
    total = Decimal("0")
    report, rejected = [], []
    with open(file_name, "r", encoding="utf-8") as f:       # closed automatically
        for line_no, line in enumerate(f, start=1):         # one line at a time
            text = line.strip()
            if not text:                                    # blank line: not an error
                continue
            parts = text.split(",")
            if len(parts) != 3:
                rejected.append((line_no, text, f"expected 3 fields, found {len(parts)}"))
                continue
            reg, name, amount_text = (p.strip() for p in parts)
            try:
                amount = Decimal(amount_text)               # exact: 1250.50 stays 1250.50
            except InvalidOperation:
                rejected.append((line_no, text, f"amount {amount_text!r} is not a number"))
                continue
            if amount < 0:
                rejected.append((line_no, text, "negative amount"))
                continue
            total += amount
            report.append(f"{name} {amount}")
    return total, report, rejected


def run(file_name):
    try:
        total, report, rejected = total_bills(file_name)
    except FileNotFoundError:
        print(f"File not found: {file_name}")
        return None
    except PermissionError:
        print(f"No permission to read: {file_name}")
        return None
    except UnicodeDecodeError as e:
        print(f"File {file_name} is not valid UTF-8: {e}")
        return None
    print("\n".join(report))                                 # one join, not repeated +
    print("Total", total)
    print(f"{len(rejected)} line(s) rejected:")
    for line_no, text, reason in rejected:
        print(f"  line {line_no}: {text!r}  ->  {reason}")
    return total


# ----------------------------------------- measurements for 50,000 lines
def make_big_file(n):
    fd, path = tempfile.mkstemp(suffix=".txt", text=True)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for i in range(n):
            f.write(f"{192300000 + i},Student {i},{1000 + i % 500}.{i % 100:02d}\n")
    return path


def by_line(path):
    total = Decimal(0)
    with open(path, encoding="utf-8") as f:
        for line in f:
            total += Decimal(line.split(",")[2])
    return total


def by_read(path):
    total = Decimal(0)
    with open(path, encoding="utf-8") as f:
        for line in f.read().split("\n"):
            if line:
                total += Decimal(line.split(",")[2])
    return total


def by_readlines(path):
    total = Decimal(0)
    with open(path, encoding="utf-8") as f:
        for line in f.readlines():
            total += Decimal(line.split(",")[2])
    return total


def measure():
    path = make_big_file(50_000)
    print(f"\nFile of 50,000 lines: {os.path.getsize(path):,} bytes")
    print(f"{'method':<22}{'time s':>9}{'peak memory (bytes)':>22}")
    results = []
    for name, fn in (("iterate lines", by_line), ("f.read().split", by_read),
                     ("f.readlines()", by_readlines)):
        tracemalloc.start()
        t0 = time.perf_counter()
        total = fn(path)
        dt = time.perf_counter() - t0
        peak = tracemalloc.get_traced_memory()[1]
        tracemalloc.stop()
        results.append(total)
        print(f"{name:<22}{dt:>9.4f}{peak:>22,}")
    print("all three give the same total:", len(set(results)) == 1, results[0])
    # repeated + versus join for the report text
    names = [f"Student {i} {1000 + i}" for i in range(50_000)]
    t0 = time.perf_counter(); r = ""
    for s in names:
        r = r + s + "\n"
    t_plus = time.perf_counter() - t0
    t0 = time.perf_counter(); r2 = "\n".join(names) + "\n"
    t_join = time.perf_counter() - t0
    print(f"report text: repeated + {t_plus:.4f} s | join {t_join:.4f} s | same: {r == r2}")
    os.remove(path)


if __name__ == "__main__":
    print_diagnosis()
    print("\nTASK 1.2  REPAIRED SCRIPT on mess_oct.txt")
    here = os.path.dirname(os.path.abspath(__file__))
    file_name = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "mess_oct.txt")
    run(file_name)
    print("\nMissing file:")
    run(os.path.join(here, "mess_dec.txt"))
    print("Expected by hand: 1250.50 + 980 + 1100.75 + 1320.25 + 1500.00 =",
          Decimal("1250.50") + 980 + Decimal("1100.75") + Decimal("1320.25") + Decimal("1500.00"))
    measure()


"""
TASK 1.3 - DESIGN DEFENCE (about 90 words)
 The repaired version takes the file name as a parameter, so any month's file can
 be used. The with statement always closes the file, even after an error. Reading one
 line at a time keeps memory constant, so 50,000 lines need no more memory than
 one. Only specific exceptions are caught: a bad amount is rejected AND recorded
 with its line number and reason, so no bill disappears silently. Decimal keeps
 paise exact, a list with join() avoids quadratic string copying, and blank
 lines are skipped on purpose.

ALTERNATIVE CONCEPT & COMPLEXITY (n lines, file size S bytes)
 - f.read() / f.readlines(): the whole file is loaded first. Time O(n) (still one pass),
   memory O(S) (read() also builds the split list: about 2 x S).
 - Iterating over the file object: time O(n), memory O(length of ONE line) = O(1) in n
   (the file object reads buffered blocks of a few KB). See the measured peak
   memory above. For 50,000 lines the difference is small in time but large in memory,
   and it grows with the file, so the iteration version is the one to use for big files.
"""
