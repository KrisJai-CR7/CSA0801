"""
Task 4 - File and Exception Forensics: the Library Returns Log (7 marks)

ORIGINAL program (kept as buggy_* functions below):

    def save_returns(books):
        log = open("returns.log", "w")
        for b in books:
            log.write(b)
        log.close()

    def process(day_file):
        try:
            books = open(day_file).read().split("\\n")
            save_returns(books)
        except FileNotFoundError:
            print("missing")
"""
import logging
import os
import shutil
import time
from pathlib import Path


# ------------------------------------------------------------ original (buggy)
def buggy_save_returns(books):
    log = open("returns.log", "w")
    for b in books:
        log.write(b)
    log.close()


def buggy_process(day_file):
    try:
        books = open(day_file).read().split("\n")
        buggy_save_returns(books)
    except FileNotFoundError:
        print("missing")


# ------------------------------------------------------------ repaired version
def setup_logging(name="library_errors.log"):
    """Call once, in the folder where the error log should be kept."""
    logging.basicConfig(filename=name, level=logging.ERROR, force=True,
                        format="%(asctime)s %(levelname)s %(message)s")


def save_returns(books, log_name="returns.log"):
    with open(log_name, "a", encoding="utf-8") as log:      # append: keeps earlier days
        for b in books:
            log.write(f"{b}\n")                              # one book per line


def process(day_file):
    try:
        with open(day_file, "r", encoding="utf-8") as f:
            books = [line.strip() for line in f if line.strip()]   # no '' for the last line
        save_returns(books)
    except FileNotFoundError:
        logging.error("day file missing: %s", day_file)
        print("missing:", day_file)
    except (OSError, UnicodeDecodeError, TypeError) as e:
        logging.exception("could not process %s", day_file)        # message + traceback SAVED
        print(f"error saved to library_errors.log: {type(e).__name__}: {e}")


def make_day_files(folder):
    paths = []
    for day, books in enumerate((["Wings of Fire", "Gitanjali"], ["Godaan", "Malgudi Days"],
                                 ["Train to Pakistan", "The Guide"]), start=1):
        p = os.path.join(folder, f"day{day}.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n".join(books) + "\n")
        paths.append(p)
    return paths


def show(name):
    with open(name, encoding="utf-8") as f:
        print(repr(f.read()))


if __name__ == "__main__":
    work = Path(__file__).resolve().parent / "demo_run"      # evidence files stay here
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()
    os.chdir(work)
    setup_logging()
    work = str(work)
    days = make_day_files(work)

    print("TASK 4.2  EVIDENCE with the ORIGINAL program (three days)")
    for d in days:
        buggy_process(d)
    print("returns.log after 3 days ->", end=" ")
    show("returns.log")
    print("  defect 1: only the LAST day's books remain (Train to Pakistan, The Guide):")
    print("            mode 'w' truncates the file every time save_returns() runs.")
    print("  defect 2: the titles are glued together ('...PakistanThe Guide'): write(b) adds no newline;")
    print("            and split('\\n') produced an extra '' item for the final newline.")

    print("\n  defect 3: what happens to the open file when write() fails:")
    log_ref = {}

    def failing_save(books):
        log = open("returns.log", "w")
        log_ref["f"] = log
        for b in books:
            log.write(b)                             # int is not a str -> TypeError
        log.close()
    try:
        failing_save(["A Book", 42])
    except TypeError as e:
        print(f"    TypeError: {e}")
    print("    log.closed =", log_ref["f"].closed,
          "-> the file stays OPEN (close() was never reached), data may stay unwritten.")
    print("    and the exception is not FileNotFoundError, so buggy_process() does not catch it:")
    print("    the program stops with a traceback and NOTHING is saved to any file.")
    log_ref["f"].close()

    print("\n  defect 4: other errors are not handled/recorded at all (bad encoding):")
    bad = os.path.join(work, "bad.txt")
    with open(bad, "wb") as f:
        f.write(b"\xff\xfe\n")
    try:
        buggy_process(bad)
    except UnicodeDecodeError as e:
        print("    uncaught UnicodeDecodeError ->", e)
    print("    also open(day_file).read() leaves the day file open (no close).")

    print("\nTASK 4.3  REPAIRED program, same three days (+ a missing day and a bad file)")
    os.remove("returns.log")
    for d in days:
        process(d)
    process(os.path.join(work, "day9.txt"))
    process(bad)
    print("returns.log ->")
    with open("returns.log", encoding="utf-8") as f:
        print(f.read())
    print("library_errors.log ->")
    with open("library_errors.log", encoding="utf-8") as f:
        text = f.read()
        print("\n".join(text.splitlines()[:2]), "\n   ...", len(text.splitlines()), "lines in total (incl. traceback)")

    # alternative concept: manual try/finally
    print("\nALTERNATIVE: manual try/finally vs with - is the file closed after a failed write?")
    handles = {}

    def manual(books, key):
        f = open(f"{key}.log", "a", encoding="utf-8")
        handles[key] = f
        try:
            for b in books:
                f.write(f"{b}\n")
        finally:
            f.close()

    def with_version(books, key):
        with open(f"{key}.log", "a", encoding="utf-8") as f:
            handles[key] = f
            for b in books:
                f.write(f"{b}\n")

    def original_style(books, key):
        f = open(f"{key}.log", "a", encoding="utf-8")
        handles[key] = f
        for b in books:
            f.write(f"{b}\n")
        f.close()
    # make write() really fail: an object whose str() raises TypeError
    class Boom:
        def __str__(self):
            raise TypeError("cannot convert")
    for label, fn in (("original style", original_style), ("manual try/finally", manual),
                      ("with statement", with_version)):
        try:
            fn(["ok", Boom()], label.split()[0] + "2")
        except TypeError:
            pass
        print(f"  {label:<20} file closed after the error: {handles[label.split()[0] + '2'].closed}")
    handles["original2"].close()

    t0 = time.perf_counter()
    for _ in range(2000):
        with open("t1.log", "a") as f:
            f.write("x\n")
    t_with = time.perf_counter() - t0
    t0 = time.perf_counter()
    for _ in range(2000):
        f = open("t2.log", "a")
        try:
            f.write("x\n")
        finally:
            f.close()
    t_try = time.perf_counter() - t0
    print(f"  2,000 open/write/close cycles: with {t_with:.4f} s | try/finally {t_try:.4f} s")


"""
TASK 4.1 - DEFECTS
 1. Earlier days are lost: save_returns() opens returns.log in mode "w", which truncates
    (empties) the file each time. To ADD to a log, the mode must be "a" (append).
 2. Books joined together: log.write(b) writes the text only; write() never adds a
    newline, so titles must be written with an explicit "\\n". (Also split("\\n") of a
    file ending with a newline gives a last empty string.)
 3. Open file when write() fails: log.close() is the last line of the function, so any
    exception in the loop (a non-string item, full disk) jumps out BEFORE close() runs.
    The file object stays open (buffered data may never be written, the file stays locked
    on Windows); the day file opened in process() is never closed either.
 4. "Stopped with an error but no message was saved": process() catches only
    FileNotFoundError and merely print()s it; any other exception is uncaught, and
    print goes to the screen, which nobody keeps. There is no error log.

TASK 4.3 - REPAIR: mode "a", "\\n" after every title, `with` for both files, blank lines
 dropped, FileNotFoundError and other expected errors caught specifically and written to
 library_errors.log with logging (logging.exception saves the traceback).

TASK 4.4 - TWO RULES THAT WOULD HAVE PREVENTED THEM
 Rule 1: always open files with a `with` statement (guaranteed close) and choose the
         mode deliberately: "w" only when you truly want to replace, "a" to add.
 Rule 2: never let an error vanish: catch specific exceptions, and WRITE the message
         (with traceback) to a persistent error log, not just print() it.
 (Also: write explicit newlines; test with several days, not one.)

ALTERNATIVE CONCEPT & COMPLEXITY - manual open()/try/finally/close() instead of `with`
 - Time: identical, O(number of books) for the writes, and the same cost per open/close
   (see the 2,000-cycle timing above). Space: identical, O(1) beyond the line being written.
   `with` is just compact syntax for try/finally, so complexity does not change.
 - Files left open after an error: with the `with` statement 0 (the context manager calls
   close() on exit even for an exception); with a correctly written try/finally 0; with the
   ORIGINAL style (close() at the end, no finally) 1 file for each failure - the log, plus the
   day file that process() opened and never closed: up to 2 per failed day, which
   accumulates over a week and can hit the operating-system limit of open files.
   Manual try/finally is also easy to get wrong (opening the file INSIDE the try, so
   finally closes a name that was never assigned).
"""
