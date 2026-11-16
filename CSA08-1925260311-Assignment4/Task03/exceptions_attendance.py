"""
Task 3 - Design the Error Handling: Exceptions in the Attendance Processor (9 marks)
"""
import os
import random
import tempfile
import time


# ============================================== the given program (completed)
class InvalidRecord(Exception):
    """Raised when a line of the attendance file is not in the expected format."""


def parse_line(line):
    """'192311001,2026-10-08,P' -> ('192311001', '2026-10-08', 'P')"""
    parts = line.strip().split(",")
    # TODO 1 (completed): raise InvalidRecord if there are not exactly 3 fields or the
    # status is not P or A; otherwise return the 3 fields as a tuple
    if len(parts) != 3:
        raise InvalidRecord(f"expected 3 fields, found {len(parts)}")
    if parts[2] not in ("P", "A"):
        raise InvalidRecord(f"invalid status {parts[2]!r}")
    return tuple(parts)


def summarise(path):
    present, absent, errors = 0, 0, []
    # TODO 2 (completed): open the file with a with statement, parse each line inside
    # try/except InvalidRecord, count P and A, and record (line number, message) for bad lines
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                try:
                    reg, date, status = parse_line(line)
                except InvalidRecord as e:
                    errors.append((line_no, str(e)))
                else:
                    if status == "P":
                        present += 1
                    else:
                        absent += 1
    except FileNotFoundError:                     # "file name that does not exist"
        errors.append((0, f"file not found: {path}"))
    return present, absent, errors


data = ("192311001,2026-10-08,P\n192311002,2026-10-08,A\n"
        "192311003,2026-10-08\n192311004,2026-10-08,L\n")
with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                 encoding="utf-8") as tmp:
    tmp.write(data)
print(summarise(tmp.name))          # file is closed (flushed) before it is read
os.remove(tmp.name)
# Expected output: (1, 1, [(3, 'expected 3 fields, found 2'), (4, "invalid status 'L'")])

print("non-existent file ->", summarise("no_such_file.csv"))


# ========================================== Task 3.1 - the failure table
FAILURES = [
    ("Missing folder", "FileNotFoundError", "open('nodir/day1.txt')"),
    ("Missing file", "FileNotFoundError", "open('day9.txt')"),
    ("Path is a folder, not a file", "IsADirectoryError (Windows: PermissionError)", "open('.')"),
    ("Permission denied", "PermissionError", "file without read permission"),
    ("Wrong encoding / binary bytes", "UnicodeDecodeError (a ValueError)", "b'\\xff' read as utf-8"),
    ("Damaged line: wrong status or field count", "InvalidRecord (custom; ValueError/IndexError if unchecked)",
     "'192311003,2026-10-08'"),
    ("Damaged line: field missing when indexed", "IndexError", "parts[2] of a 2-field line"),
    ("Damaged line: text where a number is expected", "ValueError", "int('abc')"),
    ("Empty file", "none - the loop runs zero times (result 0, 0, [])", "open('empty.txt')"),
    ("Disk full / device error while writing", "OSError", "write() to a full disk"),
]


def print_failure_table():
    print(f"\n{'Failure':<48}{'Exception':<68}Example")
    for f, e, ex in FAILURES:
        print(f"{f:<48}{e:<68}{ex}")


# ========================================== Task 3.2 - custom exception design
"""
 InvalidRecord (subclass of Exception) is RAISED in parse_line(), the only function that
 knows what a valid line looks like (it detects the problem), and HANDLED in summarise(),
 which knows what to do about it (log it and continue with the next line). parse_line()
 does not print or decide anything; summarise() does not examine the format.
 A custom class lets summarise() catch exactly this problem and nothing else, so a
 real bug (NameError, TypeError) is not mistaken for a bad line.
"""


# ========================================== Task 3.3 - the complete try statement
class ProcessingError(Exception):
    """The whole file could not be processed."""


def process_file(path):
    """try / except (specific) / else / finally and raise ... from ..."""
    f = None
    try:
        f = open(path, "r", encoding="utf-8")
        lines = f.read().splitlines()
    except FileNotFoundError as e:
        raise ProcessingError(f"{path} is missing") from e          # keeps the cause
    except PermissionError as e:
        raise ProcessingError(f"{path} cannot be read") from e
    except UnicodeDecodeError as e:
        raise ProcessingError(f"{path} is not UTF-8") from e
    else:                                  # runs only if NO exception occurred
        present = sum(1 for l in lines if l.endswith(",P"))
        print(f"   else-block: read {len(lines)} lines without error")
        return present
    finally:                               # ALWAYS runs: even after raise/return
        if f is not None:
            f.close()
        print("   finally-block: file closed (if it was opened)")


def demo_try():
    print("\nTask 3.3 complete try statement:")
    d = tempfile.mkdtemp()
    good = os.path.join(d, "good.txt")
    with open(good, "w", encoding="utf-8") as f:
        f.write("1,d,P\n2,d,A\n")
    bad_enc = os.path.join(d, "binary.txt")
    with open(bad_enc, "wb") as f:
        f.write(b"\xff\xfe,\x80\n")
    for label, p in (("good file", good), ("missing file", os.path.join(d, "x.txt")),
                     ("wrong encoding", bad_enc), ("a folder", d)):
        print(f" {label}:")
        try:
            print("   result:", process_file(p))
        except ProcessingError as e:
            print(f"   ProcessingError: {e} | original cause: {e.__cause__!r}")
        except OSError as e:                # e.g. IsADirectoryError not mapped above
            print(f"   unmapped OSError: {type(e).__name__}: {e}")


# ========================================== Task 3.4 - the misuse experiment
def summarise_misuse(path):
    present, absent, errors = 0, 0, []
    try:
        with open(path, encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                reg, date, status = parse_line(line)
                if status == "P":
                    presnt += 1                  # TYPING ERROR: should be 'present'
                else:
                    absent += 1
    except Exception:
        pass                                     # hides EVERYTHING
    return present, absent, errors


def demo_misuse():
    print("\nTask 3.4 misuse experiment on a file with 3 valid lines:")
    p = os.path.join(tempfile.mkdtemp(), "m.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write("1,d,P\n2,d,A\n3,d,P\n")
    print("  except Exception: pass ->", summarise_misuse(p),
          "(silently WRONG: the real answer is (2, 1, []))")
    try:
        present = 0
        presnt += 1
    except NameError as e:
        print("  what was hidden        ->", type(e).__name__ + ":", e)


# ========================================== alternative concept: LBYL vs EAFP
def parse_eafp(line):
    try:
        reg, date, status = line.strip().split(",")
        if status not in ("P", "A"):
            raise InvalidRecord
        return reg, date, status
    except (ValueError, InvalidRecord):
        return None


def parse_lbyl(line):
    parts = line.strip().split(",")
    if len(parts) == 3 and parts[2] in ("P", "A"):
        return tuple(parts)
    return None


def timing(bad_rate, n=200_000):
    rnd = random.Random(5)
    lines = [("1,2026-10-08,P" if rnd.random() >= bad_rate else "1,2026-10-08") for _ in range(n)]
    out = []
    for fn in (parse_eafp, parse_lbyl):
        t0 = time.perf_counter()
        for l in lines:
            fn(l)
        out.append((time.perf_counter() - t0) / n * 1e9)
    return out


if __name__ == "__main__":
    print_failure_table()
    demo_try()
    demo_misuse()
    print(f"\nTime per line (ns), {200_000:,} lines    {'try/except (EAFP)':>18}{'if-check (LBYL)':>17}")
    for rate in (0.0, 0.001, 0.5):
        a, b = timing(rate)
        print(f"  bad lines {rate:>6.1%}{'':>20}{a:>10.0f}{b:>17.0f}")


"""
TASK 3.4 explanation: `except Exception: pass` catches the error raised by the
 mistyped variable (presnt) on the very first P line and throws it away (Python
 reports it as UnboundLocalError, a subclass of NameError, because `presnt += 1`
 makes presnt a local name that has no value). The function
 then returns the initial values (0, 0, []) as if the file contained nothing, so the
 report is wrong with NO message, no traceback and no log. A specific except clause
 would let the NameError propagate and show the file, line and name at once. Catch only
 the exceptions you can actually handle.

ALTERNATIVE CONCEPT & COMPLEXITY - "easier to ask forgiveness" (try/except, the style used
 here) versus "look before you leap" (if checks before use), n lines:
 - Both are O(1) per line and O(n) overall, with O(1) extra space.
 - EAFP: the good path pays almost nothing (entering a try block is cheap in
   Python 3.11+); each BAD line is expensive: raising and catching an exception costs
   a few times the cost of a comparison. So EAFP is as fast as LBYL (a tie within
   measurement noise in the table) when bad lines are RARE, and loses when they are common.
 - LBYL: every line pays for the checks (len, in), but a bad line costs no more than
   a good one, so it wins when bad lines are COMMON (table: 212 ns against 404 ns at 50% bad lines).
 - EAFP also avoids races (a file may vanish between os.path.exists and open) and
   removes the duplicated checking logic; LBYL keeps the validation visible.
"""
