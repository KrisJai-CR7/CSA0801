"""
Task 6 - Design Challenge: College Fest Registration Desk (13 marks)

==============================================================================
STAGE 1 - INTERPRET THE PROBLEM (2 marks)
 Inputs : one text file per department (cse.txt, ece.txt, mech.txt, it.txt, aiml.txt), UTF-8,
          one registration per line:   regno,name,department,email,event1;event2;...
          Files can be missing; lines can be damaged, duplicated or have a bad e-mail.
 Outputs: output/master.csv          clean list, one row per student (events joined by ;)
          output/events/<event>.txt  participants of each event
          output/summary.txt         counts and per-department / per-event totals
          output/errors.log          every rejected / merged line and file problem
 Rules  : a register number is 9 digits; name, department, events not empty; e-mail valid
          (see validator.py); a student registered twice appears once, with the events of both.
 TESTABLE REQUIREMENTS
   R1  A valid line appears exactly once in master.csv with its events.
   R2  A register number found twice gives ONE master row whose events are the union.
   R3  A line with an invalid e-mail is NOT in master.csv and is in errors.log (kind "bad e-mail").
   R4  A damaged line (wrong field count, bad register number, empty field) is skipped and
       logged with file name and line number.
   R5  A missing department file is logged and the other files are still processed.
   R6  The program finishes (exit code 0, all four outputs written) whatever the input.
   R7  Event files contain exactly the master-list students who chose that event.
   R8  Duplicate detection takes O(1) average time per registration.

STAGE 2 - PROCESSING FLOW (2 marks)
   input files (one per department)
        |  reader.read_lines()      -- file missing / permission / encoding  --> errors.log
        v
   (line_number, text) ... one line at a time
        |  validator.parse_registration()  -- wrong fields / bad regno / bad e-mail --> errors.log (skip line)
        v
   valid record
        |  processor: regno in seen_set ?  -- yes --> merge events, note in errors.log
        v                                   -- no  --> add to people{} and seen_set
   people {regno: record}
        |  writer.write_master()  write_event_lists()  write_summary()  write_error_log()
        v
   master.csv   events/*.txt   summary.txt   errors.log

STAGE 3 - CRITICAL DESIGN DECISIONS (2 marks)
 * Duplicates: a SET of register numbers already seen (O(1) average membership test); the
   first record wins for name/e-mail and the events of later records are merged in. A list
   search would be O(n) per registration, O(n^2) overall (measured below).
 * E-mail validation with string methods: count('@') == 1, no spaces, local part checked with
   replace() + isalnum(), domain split('.') with no empty label, last label alphabetic and
   at least 2 letters. A line with an invalid e-mail is REJECTED (the committee cannot
   contact the student) but reported, never dropped silently.
 * Exceptions: FileNotFoundError / PermissionError / IsADirectoryError / UnicodeDecodeError /
   OSError are handled in reader.py (the only place that touches input files) and returned as
   a "problem"; the custom InvalidRecord (kind = damaged | bad e-mail) is RAISED in
   validator.py and HANDLED in processor.py, which decides to skip and log. One last-resort
   `except Exception` per line records an unexpected bug in errors.log and continues, so
   R6 holds; it never uses `pass`.

STAGE 4 - PACKAGE AND PSEUDOCODE (4 marks)
 fest/__init__.py   exports run_pipeline, InvalidRecord, is_valid_email, parse_registration
 fest/reader.py     read_lines(path) -> (lines, problem)
 fest/validator.py  InvalidRecord, is_valid_email(email), parse_registration(line)
 fest/writer.py     write_master, write_event_lists, write_error_log, write_summary, slug
 fest/processor.py  run_pipeline(input_dir, output_dir, departments)
 run_demo.py        creates demo inputs, runs the package, shows the test cases and timings

    ALGORITHM RunPipeline(input_dir, output_dir, departments)
    INPUT  : folder of department files, list of department names
    OUTPUT : master.csv, event files, summary.txt, errors.log
    BEGIN
        people <- empty dictionary; seen <- empty set; errors <- empty list
        FOR EACH dept IN departments DO
            (lines, problem) <- ReadLines(input_dir / dept + ".txt")
            IF problem is not empty THEN
                APPEND (file, problem) TO errors ; CONTINUE
            END IF
            FOR EACH (line_number, text) IN lines DO
                TRY
                    record <- ParseRegistration(text)          // may RAISE InvalidRecord
                CATCH InvalidRecord
                    APPEND (file, line_number, kind, message) TO errors ; CONTINUE
                END TRY
                IF record.regno IN seen THEN
                    people[record.regno].events <- people[record.regno].events UNION record.events
                    APPEND duplicate note TO errors
                ELSE
                    ADD record.regno TO seen ; people[record.regno] <- record
                END IF
            END FOR
        END FOR
        WriteMaster(people) ; WriteEventLists(people) ; WriteSummary(...) ; WriteErrorLog(errors)
    END

    ALGORITHM ParseRegistration(line)
        parts <- split line on "," and strip each
        IF count(parts) != 5 THEN RAISE InvalidRecord("damaged")
        IF regno is not 9 digits, or name/department empty, or no events THEN RAISE InvalidRecord("damaged")
        IF NOT IsValidEmail(email) THEN RAISE InvalidRecord("bad e-mail")
        RETURN record
==============================================================================
"""
import random
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from fest import is_valid_email, run_pipeline            # noqa: E402

DEPARTMENTS = ["cse", "ece", "mech", "it", "aiml"]       # mech.txt is MISSING on purpose

INPUT = {
    "cse.txt": [
        "192311001,Arun Kumar,CSE,arun@mail.com,Dance;Quiz",
        "192311002,Bala Murugan,CSE,bala.m@mail.com,Quiz",
        "192311003,Chitra Devi,CSE,chitra@mail,Singing",              # invalid e-mail (no dot)
        "192311004,Dinesh,CSE,dinesh@mail.com,Drama",
        "192311001,Arun Kumar,CSE,arun@mail.com,Singing",            # duplicate, same file
    ],
    "ece.txt": [
        "192312001,Elango,ECE,elango@college.edu.in,Dance",
        "192312002,Farook Ali,ECE,farook@@mail.com,Quiz",            # invalid e-mail (two @)
        "192312003,Gayathri",                                         # damaged: 2 fields
        "abc123456,Hari,ECE,hari@mail.com,Drama",                    # damaged: register number
        ",Indu,ECE,indu@mail.com,Dance",                             # damaged: empty regno
    ],
    "it.txt": [
        "192314001,Jothi,IT,jothi@mail.com,quiz;dance",              # events in lower case
        "192314002,Karthik,IT,karthik@mail.com,",                    # damaged: no events
        "192311004,Dinesh,CSE,dinesh@mail.com,Dance",                # duplicate across files
    ],
    "aiml.txt": [
        "192315001,Lakshmi,AIML,lakshmi@mail.com,Drama;Singing",
        "192315002,Mani,AIML,mani@mail.com,Quiz",
        "192315003,Nila,AIML,nila mail@x.com,Quiz",                  # invalid e-mail (space)
    ],
}


def ensure_input(folder):
    folder.mkdir(exist_ok=True)
    for name, lines in INPUT.items():
        (folder / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    (folder / "mech.txt").unlink(missing_ok=True)


def test_table(people, stats, errors, out):
    log = (out / "errors.log").read_text(encoding="utf-8")
    master = (out / "master.csv").read_text(encoding="utf-8")
    events = {p.stem: p.read_text(encoding="utf-8").splitlines() for p in (out / "events").glob("*.txt")}
    checks = [
        ("R1 clean file / valid line appears once",
         master.count("192311002") == 1 and master.count("192315001") == 1),
        ("R2 duplicate merged (192311001: Dance;Quiz;Singing)",
         people["192311001"]["events"] == {"Dance", "Quiz", "Singing"} and master.count("192311001") == 1),
        ("R2b duplicate in another file merged (192311004: Dance;Drama)",
         people["192311004"]["events"] == {"Dance", "Drama"}),
        ("R3 invalid e-mails rejected and logged (3)",
         stats["bad_email"] == 3 and "192311003" not in master and log.count("bad e-mail") == 3),
        ("R4 damaged lines skipped and logged with line number (4)",
         stats["damaged"] == 4 and "ece.txt:3: damaged" in log and "it.txt:2: damaged" in log),
        ("R5 missing department file logged, others processed",
         stats["files_problem"] == 1 and "mech.txt: file problem: department file is missing" in log
         and stats["files_read"] == 4),
        ("R6 run finished, all outputs exist",
         all((out / n).exists() for n in ("master.csv", "summary.txt", "errors.log", "events"))),
        ("R7 event list = master students who chose it (Quiz: 192311001,192311002,192314001,192315002)",
         [l.split(",")[0] for l in events["quiz"]] == ["192311001", "192311002", "192314001", "192315002"]),
    ]
    for label, ok in checks:
        print(f"   [{'PASS' if ok else 'FAIL'}] {label}")
    return all(ok for _, ok in checks)


def make_registrations(n):
    rnd = random.Random(7)
    return [f"{192300000 + rnd.randrange(n * 2)}" for _ in range(n)]          # some repeats


def seen_with_set(regs):
    seen, dups = set(), 0
    for r in regs:
        if r in seen:
            dups += 1
        else:
            seen.add(r)
    return dups


def seen_with_list(regs):
    seen, dups = [], 0
    for r in regs:
        if r in seen:                       # linear search through all earlier registrations
            dups += 1
        else:
            seen.append(r)
    return dups


if __name__ == "__main__":
    inp, out = HERE / "input", HERE / "output"
    shutil.rmtree(out, ignore_errors=True)
    ensure_input(inp)

    print("STAGE 5 - IMPLEMENT AND DEMONSTRATE (5 departments, mech.txt missing)")
    people, stats, errors, summary = run_pipeline(inp, out, DEPARTMENTS)
    print("\nsummary.txt:\n" + summary)
    print("\nerrors.log:\n" + (out / "errors.log").read_text(encoding="utf-8"))
    print("master.csv:\n" + (out / "master.csv").read_text(encoding="utf-8"))
    print("event files:", sorted(p.name for p in (out / "events").glob("*.txt")))

    print("\nTEST CASES (clean files, duplicate, invalid e-mail, damaged line, missing file)")
    ok = test_table(people, stats, errors, out)
    print("   all requirements met:", ok)

    print("\nE-MAIL VALIDATOR (string methods only)")
    for e in ["a@b.com", "a.b+c@mail.co.in", "a@b", "a@@b.com", "@b.com", "a@.com", "a@b..com",
              "a b@c.com", "a@b.c", "", "plain"]:
        print(f"   {e!r:<22}{is_valid_email(e)}")

    print("\nROBUSTNESS: a folder instead of a file, and a binary file")
    bad = HERE / "input_bad"
    shutil.rmtree(bad, ignore_errors=True)
    bad.mkdir()
    (bad / "cse.txt").mkdir()                                 # folder named like a file
    (bad / "ece.txt").write_bytes(b"\xff\xfe\x00bad")         # not UTF-8
    _, st, errs, _ = run_pipeline(bad, bad / "out", ["cse", "ece"])
    print("   finished:", st["files_problem"] == 2, "|", [(e[0], e[3]) for e in errs])
    shutil.rmtree(bad)

    print("\nALTERNATIVE: duplicate check with a list vs a set")
    print(f"   {'n':>8}{'set s':>10}{'list s':>10}{'list/set':>10}  same count")
    for n in (1_000, 4_000, 16_000):
        regs = make_registrations(n)
        t0 = time.perf_counter(); a = seen_with_set(regs); t1 = time.perf_counter() - t0
        t0 = time.perf_counter(); b = seen_with_list(regs); t2 = time.perf_counter() - t0
        print(f"   {n:>8,}{t1:>10.5f}{t2:>10.5f}{t2 / t1:>10.1f}  {a == b}")


"""
ALTERNATIVE CONCEPT & COMPLEXITY (n registrations, d distinct register numbers)
 - Search a LIST of all earlier registrations: each test `regno in seen_list` compares with
   up to d items -> O(d) per registration, O(n * d) = O(n^2) in total when most are distinct.
   Space O(d).
 - Keep a SET of register numbers already seen: hashing makes the membership test O(1) on
   average -> O(n) in total. Space O(d) as well (a hash table: a constant factor more
   memory per entry than a list).
 - Measured: each time n grows 4x (1,000 -> 4,000 -> 16,000) the list time grows by about
   8x and then 17x (approaching the 16x of a quadratic), while the set time grows by only
   about 3-5x (linear); at 16,000 registrations the list version is over 500 times slower.
   The set trades a little memory for a huge saving in time.
"""
