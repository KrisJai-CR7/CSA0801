"""
Task 2 - From Requirement to File-Processing Design: Biometric Attendance Files (8 marks)

Task 2.1 - MODEL THE DATA
 Input : one text file per classroom per day, inside input/, UTF-8, one record per line:
             register_number,date,status        e.g.  192311001,2026-10-08,P
         status is P (present) or A (absent). Damaged lines: missing fields, wrong
         status letter, blank register number or date, extra commas.
 Data structures to accumulate (all built in ONE pass over every file):
         present = {register_number: number_of_P}
         total   = {register_number: number_of_valid_records}
         damaged = [(file_name, line_number, reason, text)]
 Outputs (in output/):
   1. attendance_report.csv  header + one line per student:
        register_number,present,total,percentage     (percentage = 100 x present / total, 2 decimals)
      plus below_75.txt : one line per student with percentage < 75
        register_number,percentage
   2. damaged_lines.log : one line per bad record
        file_name:line_number: reason: original text

Task 2.2 - FILE OPERATIONS
  * Input files  : mode "r" (read only, so the originals can never be damaged),
                   encoding="utf-8" stated explicitly (not the OS default),
                   iterated line by line (for line in f) - never f.read().
  * Report files : mode "w" (a fresh report each run; running twice must not duplicate
                   rows), newline="" for the csv.
  * Damaged log  : mode "w" here (one log per run); "a" would be used if the log
                   had to keep the history of several runs.
  * pathlib.Path.glob("*.txt") lists the daily files; sorted() makes the order stable.
  * `with` for every file; write() with explicit "\\n".

Task 2.3 - PSEUDOCODE (SIMATS Engineering - Standard for Algorithmic Pseudocode)
    ALGORITHM ProcessMonth(input_dir, output_dir)
    INPUT  : input_dir  - folder of daily attendance files
    OUTPUT : attendance_report.csv, below_75.txt, damaged_lines.log
    BEGIN
        present <- empty dictionary
        total   <- empty dictionary
        damaged <- empty list
        FOR EACH file IN sorted list of "*.txt" files in input_dir DO
            TRY
                OPEN file for reading (utf-8)
                line_number <- 0
                FOR EACH line IN file DO
                    line_number <- line_number + 1
                    IF line is blank THEN CONTINUE
                    fields <- split line on ","
                    IF number of fields != 3 OR any field is empty THEN
                        APPEND (file, line_number, "bad field count") TO damaged
                    ELSE IF status NOT IN {"P", "A"} THEN
                        APPEND (file, line_number, "invalid status") TO damaged
                    ELSE
                        total[register] <- total.get(register, 0) + 1
                        IF status = "P" THEN present[register] <- present.get(register, 0) + 1
                    END IF
                END FOR
            CATCH file cannot be read (missing, permission, encoding)
                APPEND (file, 0, reason) TO damaged
            END TRY
        END FOR
        WRITE the report rows (sorted by register number) and below_75 rows
        WRITE damaged lines to the log
    END
"""
import csv
import os
import random
import shutil
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


# ------------------------------------------------------------ sample data
SAMPLE = {
    "2026-10-01.txt": ["192311001,2026-10-01,P", "192311002,2026-10-01,P",
                       "192311003,2026-10-01,A", "192311004,2026-10-01,P"],
    "2026-10-02.txt": ["192311001,2026-10-02,P", "192311002,2026-10-02,A",
                       "192311003,2026-10-02,A", "192311004,2026-10-02,P"],
    "2026-10-03.txt": ["192311001,2026-10-03,A", "192311002,2026-10-03,P",
                       "192311003,2026-10-03,X",          # wrong status letter
                       "192311004,2026-10-03,P", "192311005,2026-10-03,P"],
    "2026-10-04.txt": ["192311001,2026-10-04,P", "192311002,2026-10-04,P",
                       "192311003,2026-10-04",            # missing field
                       "192311004,2026-10-04,P", "", "192311005,2026-10-04,A"],
}


def ensure_sample_input(input_dir):
    input_dir.mkdir(exist_ok=True)
    if not any(input_dir.glob("*.txt")):
        for name, lines in SAMPLE.items():
            (input_dir / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


# ------------------------------------------------------------ processing
def process_month(input_dir, output_dir, verbose=False):
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    present, total, damaged = {}, {}, []
    for path in sorted(input_dir.glob("*.txt")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                    text = line.strip()
                    if not text:
                        continue
                    fields = [x.strip() for x in text.split(",")]
                    if len(fields) != 3 or not all(fields):
                        damaged.append((path.name, line_no, "bad field count", text))
                        continue
                    reg, date, status = fields
                    if status not in ("P", "A"):
                        damaged.append((path.name, line_no, f"invalid status {status!r}", text))
                        continue
                    total[reg] = total.get(reg, 0) + 1
                    if status == "P":
                        present[reg] = present.get(reg, 0) + 1
                    if verbose:
                        print(f"   {path.name} line {line_no}: {reg} {status} -> "
                              f"present={present.get(reg, 0)} total={total[reg]}")
        except (OSError, UnicodeDecodeError) as e:
            damaged.append((path.name, 0, f"file not processed: {e}", ""))

    output_dir.mkdir(exist_ok=True)
    rows = []
    for reg in sorted(total):
        p = present.get(reg, 0)
        rows.append((reg, p, total[reg], round(100 * p / total[reg], 2)))
    with open(output_dir / "attendance_report.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["register_number", "present", "total", "percentage"])
        w.writerows(rows)
    with open(output_dir / "below_75.txt", "w", encoding="utf-8") as f:
        for reg, p, t, pct in rows:
            if pct < 75:
                f.write(f"{reg},{pct}\n")
    with open(output_dir / "damaged_lines.log", "w", encoding="utf-8") as f:
        for name, line_no, reason, text in damaged:
            f.write(f"{name}:{line_no}: {reason}: {text}\n")
    return rows, damaged


# ---------------------------------------------- alternative: re-read per student
def per_student_rereading(input_dir, students):
    """Alternative design: for EVERY student read ALL files again: O(s * f * l)."""
    result = {}
    for reg in students:
        p = t = 0
        for path in sorted(Path(input_dir).glob("*.txt")):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) == 3 and parts[0] == reg and parts[2] in ("P", "A"):
                        t += 1
                        p += parts[2] == "P"
        result[reg] = round(100 * p / t, 2) if t else 0
    return result


def make_month(directory, s, f, seed=1):
    rnd = random.Random(seed)
    regs = [f"{192300000 + i}" for i in range(s)]
    for d in range(f):
        with open(Path(directory) / f"day{d:02d}.txt", "w", encoding="utf-8") as fh:
            for r in regs:
                fh.write(f"{r},2026-10-{d + 1:02d},{rnd.choice('PPPA')}\n")
    return regs


if __name__ == "__main__":
    inp, out = HERE / "input", HERE / "output"
    ensure_sample_input(inp)
    print("TASK 2.4  TRACE of the pseudocode for one small file (2026-10-04.txt, "
          "contains a damaged line and a blank line):")
    tmp = Path(tempfile.mkdtemp())
    shutil.copy(inp / "2026-10-04.txt", tmp / "2026-10-04.txt")
    rows, damaged = process_month(tmp, tmp / "out", verbose=True)
    print("   damaged ->", damaged)
    shutil.rmtree(tmp)

    print("\nFull month:")
    rows, damaged = process_month(inp, out)
    print(f"{'register':<12}{'present':>8}{'total':>7}{'percent':>9}")
    for r in rows:
        print(f"{r[0]:<12}{r[1]:>8}{r[2]:>7}{r[3]:>9}")
    print("below 75%:", (out / "below_75.txt").read_text().split())
    print("damaged_lines.log:")
    print((out / "damaged_lines.log").read_text())
    print("hand check: 192311001 -> P,P,A,P = 3/4 = 75.0 (not below 75); "
          "192311003 -> A,A,(X rejected),(missing field rejected) = 0/2 = 0.0")

    print("\nCOMPARISON: one pass with dictionary vs re-reading per student (f = 20 files)")
    print(f"{'students s':>11}{'lines/file l':>14}{'one pass s':>12}{'per-student s':>15}  same")
    for s in (50, 100, 200):
        d = Path(tempfile.mkdtemp())
        regs = make_month(d, s, 20)
        t0 = time.perf_counter(); one, _ = process_month(d, d / "o"); t1 = time.perf_counter() - t0
        t0 = time.perf_counter(); two = per_student_rereading(d, regs); t2 = time.perf_counter() - t0
        same = {r[0]: r[3] for r in one} == two
        print(f"{s:>11}{s:>14}{t1:>12.4f}{t2:>15.4f}  {same}")
        shutil.rmtree(d)


"""
ALTERNATIVE CONCEPT & COMPLEXITY (s students, f files, l lines per file)
 - Re-reading all the files for every student: time O(s * f * l) line reads
   (each of the s students scans all f*l lines), space O(1) for the counters of the
   current student.   Since l grows with s (every student appears in each file) this is O(s^2 * f).
 - One pass with a dictionary: time O(f * l) - every line is read once, space
   O(s) for the two dictionaries (one entry per student).
 - Measured above: the per-student version becomes about 3x slower for each doubling
   of s (heading towards 4x), while the one-pass version takes less than 2x longer; at
   s = 200 it is about 65x slower. Trade-off: O(s) memory for the dictionaries is
   tiny compared with the saved reads.
"""
