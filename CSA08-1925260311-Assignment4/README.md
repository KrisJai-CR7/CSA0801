# CSA08-1925260311-Assignment4

**Student:** V.Jaikrish  **Register number:** 1925260311
**Course:** Python Programming (CSA08) - Assignment 4 (CO4): robust data processing with
files, exceptions, modules and packages - B.Tech (AI and ML), SIMATS

## Python version
Python 3.12 (3.9+ works). No external libraries (`requirements.txt` not needed): only the
standard library (`pathlib`, `csv`, `logging`, `decimal`, `tempfile`, `tracemalloc`,
`subprocess`, `time`, `random`, `shutil`).

## How to run (from inside the task folder)
```
cd Task01 && python mess_bills.py
cd Task02 && python attendance_processor.py
cd Task03 && python exceptions_attendance.py
cd Task04 && python library_returns.py
cd Task05 && python compare_organisations.py          # runs all four organisations
cd Task06 && python run_demo.py
```

## Tasks and result of each
| Folder | Task | Result |
|---|---|---|
| Task01 | Diagnose and repair the mess-bill script (6) | 8 design deficiencies explained; repaired `total_bills(file_name)` with `with`, line-by-line reading, `Decimal`, specific exceptions and a list of rejected lines (total 6151.50, 3 rejected); 50,000-line memory/time measurements |
| Task02 | Biometric attendance files (8) | data model, file modes, pseudocode, trace; reports `attendance_report.csv`, `below_75.txt`, `damaged_lines.log` in `output/`; one-pass dictionary vs re-reading per student |
| Task03 | Exceptions in the attendance processor (9) | `parse_line` / `summarise` completed (output `(1, 1, [(3, 'expected 3 fields, found 2'), (4, "invalid status 'L'")])`), failure table, custom `InvalidRecord`, complete `try` statement with `raise ... from`, misuse experiment, EAFP vs LBYL timings |
| Task04 | Library returns log forensics (7) | four defects demonstrated with a three-day test; repaired program (append mode, newlines, `with`, error log); manual `try/finally` vs `with` |
| Task05 | Same utility organised four ways (7) | (a) one script, (b) one module, (c) three modules, (d) package `attendance/`; identical output; second report added to each (files changed 1 / 2 / 3 / 4); import forms, naming conflict, import cost |
| Task06 | Fest registration desk design challenge (13) | package `fest/` (reader, validator, writer, processor); 8 requirements tested (all PASS); missing file, duplicates, invalid e-mails, damaged lines; set vs list duplicate check |

Every program prints its evidence; the written answers (explanations, pseudocode, Big-O
comparisons, decisions) are in the docstring/comment blocks of each file. Timings vary from one
computer to another.

## Still to be added by the student
Output screenshots for every task, the report (diagnoses, designs, pseudocode, failure tables,
comparisons), and the repository link: **GitHub Repository Link:** ______________________
(at least one commit per task is required).
