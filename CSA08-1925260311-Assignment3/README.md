# CSA08-1925260311-Assignment3

**Student:** V.Jaikrish  **Register number:** 1925260311
**Course:** Python Programming (CO3 - lists, tuples, dictionaries and sets),
B.Tech (Artificial Intelligence and Machine Learning), SIMATS

## Python version
Python 3.12. No external libraries (`requirements.txt` not needed; only the
standard library: `random`, `time`, `copy`, `sys`, `re`, `string`, `collections`).

## How to run
```
cd Task01 && python q1_rainfall.py
cd Task02 && python q2_tuples_copying.py
cd Task03 && python q3_complaints.py
cd Task04 && python q4_electives_sets.py
cd Task05 && python q5_sensor_cleaning.py
cd Task06 && python q6_railway_timetable.py
cd Task07 && python q7_contact_merger.py
```

## Tasks and result of each
| Folder | Question | Result |
|---|---|---|
| Task01 | Q1 Lists and slicing (6) | weekly totals, max/min positions, 7-day moving average (naive vs running sum vs deque), dry days; addition counts 6(n-6) vs 6+2(n-7) confirmed (ratio 3.0) |
| Task02 | Q2 Tuples, mutability, copying (7) | `[[0]*c]*r` bug shown with `is`/`id()`, fixed grid; alias / shallow / deep copy; list vs tuple memory and speed; list inside a tuple |
| Task03 | Q3 Dictionaries (7) | `frequencies()` and `top()` completed (output `[('seeds', 3), ('price', 2), ('received', 2)]`); dict vs `list.count()` vs `Counter` at 1,000 / 10,000 / 100,000 complaints |
| Task04 | Q4 Sets (7) | clash / exactly one / neither with set operators (matches expected output); `x in list` vs `x in set`; nested loops vs `&` |
| Task05 | Q5 List comprehension (6) | loop vs comprehension vs map/filter, enumerate alarm minutes, dict/set comprehensions, list vs generator memory |
| Task06 | Q6 Nested data (7) | railway timetable (5 trains), station/day query sorted with `key=lambda`, station index, timings for 100 / 1,000 / 10,000 trains |
| Task07 | Q7 Contact merger (10) | 4-stage design: normalisation, dictionary + union-find merge, hand-checked test, timings for 1,000 and 100,000 contacts |

Every program prints its predictions, observed results and measurements; the
written answers (explanations, Big-O analysis, decisions) are in the comment
block at the end of each file. Timings vary from one computer to another.

## Still to be added by the student
Output screenshots for every task, the report (Q1-Q7 evidence with tables/graphs),
and the repository link: **GitHub Repository Link:** ______________________
(at least one commit per task is required).
