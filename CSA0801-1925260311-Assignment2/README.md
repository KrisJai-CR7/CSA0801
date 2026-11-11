# CSA08-1925260311-Assignment2

**Student:** V.Jaikrish  **Register number:** 1925260311
**Course:** B.Tech (Artificial Intelligence and Machine Learning), SIMATS

## Python version
Python 3.12 (needs Python 3.10+ because Q1 uses `match-case`).
No external libraries (`requirements.txt` not needed - only `time`, `io`, `re`,
`sys`, `csv`, `functools`, `tracemalloc` from the standard library).

## How to run
```
cd Task01 && python q1_subsidy.py
cd Task02 && python q2_otp.py
cd Task03 && python q3_vehicle_validator.py
cd Task04 && python q4_sms_statement.py
cd Task05 && python q5_canteen_functions.py
cd Task06 && python q6_temple_steps.py
cd Task07 && python q7_diagnose_redesign_validate.py     # also writes q7_results.csv
```

## Tasks
| Folder | Question | What the program shows |
|---|---|---|
| Task01 | Q1 Decisions with many boundaries | separate `if` vs `if-elif-else`, match-case, lookup table; 8 predicted households |
| Task02 | Q2 Loops that count attempts | `while` vs `for range(3)`, break/continue/pass, loop `else`, changed condition, recursion |
| Task03 | Q3 Vehicle registration validator | `normalise`, `is_valid`, `format_reg` with slicing; regex comparison |
| Task04 | Q4 SMS bill statement | `+=` vs `join()` vs f-string vs `StringIO`; timings at 1,000 / 10,000 / 200,000 lines |
| Task05 | Q5 Canteen order system | mutable default argument bug, fix, closure, scope (`global`, `nonlocal`) |
| Task06 | Q6 Temple steps recursion | naive vs memoised vs loop, call tree, call counts, `RecursionError` |
| Task07 | Q7 Diagnose, redesign, validate | recursion bottleneck diagnosed and redesigned as an O(n) loop |

Every program prints predictions, observed results and counts. The written answers
(explanations, Big-O analysis, decisions) are in the comment blocks of each file.
Timing values vary from one computer to another.

## Evidence still to be added by the student
Output screenshots of each run, the three-run averages for Q4 on your own
machine, and the GitHub link: **GitHub Repository Link:** ______________
(commit each task separately - at least one commit per task is required).
