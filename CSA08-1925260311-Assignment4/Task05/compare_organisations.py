"""
Task 5 - The Same Utility Organised Four Ways (7 marks)

Task 5.1  Four organisations (all working, same output):
   (a) a_single_script/attendance_all.py            everything in one script
   (b) b_module/attendance_lib.py + main_b.py       one module imported by a main script
   (c) c_three_modules/reader.py, stats.py, report.py + main_c.py   three modules, one folder
   (d) d_package/attendance/__init__.py, reader.py, stats.py, report.py + main_d.py   a package
   `if __name__ == "__main__":` is used where code must run only when the file is executed
   (main scripts, self-tests) and NOT when it is imported (the modules are import-safe).

Task 5.2  Change of requirement: a second report (students absent for three consecutive
   days). Every line added for it carries the marker  "# 5.2 NEW".  This program counts the
   files that contain the marker = the files that had to change.

Run this file to produce all the evidence:   python compare_organisations.py
"""
import statistics
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORGS = {
    "(a) one script": ("a_single_script", "attendance_all.py"),
    "(b) one module": ("b_module", "main_b.py"),
    "(c) three modules": ("c_three_modules", "main_c.py"),
    "(d) package": ("d_package", "main_d.py"),
}


def run_main(folder, script):
    out = subprocess.run([sys.executable, script], cwd=HERE / folder,
                         capture_output=True, text=True)
    return out.stdout, out.returncode


def code_files(folder):
    return sorted(p for p in (HERE / folder).rglob("*.py"))


def main():
    print("1. SAME OUTPUT FROM ALL FOUR ORGANISATIONS")
    outputs = {}
    for name, (folder, script) in ORGS.items():
        text, code = run_main(folder, script)
        outputs[name] = text
        print(f"   {name:<20} exit code {code}, {len(text.splitlines())} lines")
    print("   identical output:", len(set(outputs.values())) == 1)
    print("   last lines:", outputs["(d) package"].splitlines()[-2:])

    print("\n2. TASK 5.2 - FILES THAT HAD TO CHANGE FOR THE SECOND REPORT")
    print(f"   {'organisation':<20}{'files':>6}{'lines':>7}{'files changed':>15}{'lines added':>13}   which files")
    for name, (folder, _) in ORGS.items():
        files = code_files(folder)
        changed, added, total = [], 0, 0
        for p in files:
            lines = p.read_text(encoding="utf-8").splitlines()
            total += len(lines)
            n = sum("# 5.2 NEW" in l for l in lines)
            if n:
                changed.append(p.name)
                added += n
        print(f"   {name:<20}{len(files):>6}{total:>7}{len(changed):>15}{added:>13}   {', '.join(changed)}")

    print("\n3. WHERE IS THE FUNCTION? (effort to find three_day_absentees)")
    for name, (folder, _) in ORGS.items():
        for p in code_files(folder):
            for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
                if line.startswith("def three_day_absentees"):
                    n = len(p.read_text(encoding="utf-8").splitlines())
                    print(f"   {name:<20}{p.relative_to(HERE)}  line {i} of {n}")

    print("\n4. THE THREE IMPORT FORMS (names created in the importing program)")
    sys.path.insert(0, str(HERE / "d_package"))
    for stmt in ("import attendance.stats", "from attendance import stats",
                 "from attendance.stats import percentage"):
        ns = {}
        exec(stmt, ns)
        names = [k for k in ns if not k.startswith("__")]
        usage = {"import attendance.stats": "attendance.stats.percentage(3, 4)",
                 "from attendance import stats": "stats.percentage(3, 4)",
                 "from attendance.stats import percentage": "percentage(3, 4)"}[stmt]
        print(f"   {stmt:<42} binds {names} -> call as {usage} = {eval(usage, ns)}")
    print("   all three load the module attendance.stats ONCE:",
          "attendance.stats" in sys.modules)

    print("\n5. NAMING CONFLICT: a different stats.py earlier on the search path")
    other = Path(tempfile.mkdtemp())
    (other / "stats.py").write_text("def percentage(a, b):\n    return 'WRONG MODULE'\n")
    code = textwrap.dedent(f"""
        import sys
        sys.path[:0] = [{str(HERE / 'c_three_modules')!r}, {str(other)!r}]   # other folder wins
        import stats                       # (c) top-level name
        print('   (c) import stats           ->', stats.__file__.split('/')[-2], stats.percentage(3, 4))
        sys.path.insert(0, {str(HERE / 'd_package')!r})
        import attendance.stats as s2
        print('   (d) attendance.stats       ->', s2.__file__.split('/')[-2], s2.percentage(3, 4))
    """)
    print(subprocess.run([sys.executable, "-c", code], capture_output=True, text=True).stdout.rstrip())

    print("\n6. ONE-TIME IMPORT COST (fresh interpreter, mean of 5 runs, milliseconds)")
    probes = {
        "(a) import attendance_all": ("a_single_script", "import attendance_all"),
        "(b) import attendance_lib": ("b_module", "import attendance_lib"),
        "(c) import reader, stats, report": ("c_three_modules", "import reader, stats, report"),
        "(d) import attendance": ("d_package", "import attendance"),
    }
    print(f"   {'statement':<36}{'first import':>13}{'second import':>14}{'tracemalloc KB':>16}")
    for label, (folder, stmt) in probes.items():
        first, second, mem = [], [], []
        for _ in range(5):
            code = textwrap.dedent(f"""
                import sys, time, tracemalloc
                sys.path.insert(0, {str(HERE / folder)!r})
                tracemalloc.start()
                t0 = time.perf_counter(); {stmt}; t1 = time.perf_counter(); {stmt}; t2 = time.perf_counter()
                print((t1 - t0) * 1000, (t2 - t1) * 1000, tracemalloc.get_traced_memory()[0] / 1024)
            """)
            a, b, c = map(float, subprocess.run([sys.executable, "-c", code], capture_output=True,
                                                text=True).stdout.split())
            first.append(a); second.append(b); mem.append(c)
        print(f"   {label:<36}{statistics.mean(first):>13.3f}{statistics.mean(second):>14.4f}"
              f"{statistics.mean(mem):>16.1f}")
    print("   (the second import only looks the module up in sys.modules)")


if __name__ == "__main__":
    main()


"""
TASK 5.3 - COMPARING THE ORGANISATIONS
                 (a) one script      (b) one module        (c) three modules       (d) package
 Readability     one long file;      better: the main      each file has ONE       best for big programs:
                 fine for 60 lines,  script is a short     job and a short name;   the folder tree shows
                 hard beyond 500     story; the module     reader/stats/report     the structure and the
                 (must scroll)       is still one file     are easy to find        import path names the job
 Reuse           copy-paste or       import the module     import only the part    `from attendance import ...`
                 import the whole    in any program         you need; modules       works anywhere the package
                 script               (needs to be on       must sit beside the     is installed/on the path
                                      the search path)      user                    and can be versioned
 Testing         only the whole      functions can be      each module is tested   each module is tested alone
                 program, or import  imported and tested   alone (stats needs no   (and the package as a unit);
                 it (guard needed)   from a test file      files at all)           tests can mirror the tree
 Naming          none inside one     one name to           top-level names like    names live INSIDE the
 conflicts       file, but a big     protect (the module   stats, reader, report   namespace `attendance.`
                 global namespace    name)                 can clash with other    (section 5 shows the clash
                                                           folders/libraries       in (c) and no clash in (d))
 Change effort   see section 2: the number of files that changed grows with the number
 (5.2)           of modules: 1, 2, 3 and 4 (d: stats, report, __init__ re-export, main).
                 More files = more places to touch, BUT each edit is small and local, and
                 the file names tell you where to look (section 3).

 import attendance.stats           binds the name `attendance` only; the function must be
                                    called with the FULL path attendance.stats.percentage().
                                    Clear origin, no clash.
 from attendance import stats      binds the name `stats` (the sub-module object); call as
                                    stats.percentage(). A short alias, still shows the origin.
 from attendance.stats import percentage   binds the function name `percentage` directly;
                                    shortest, but the origin is hidden and the name may
                                    overwrite or be overwritten by another `percentage`.

ALTERNATIVE CONCEPT & COMPLEXITY - ALL FUNCTIONS IN ONE SCRIPT INSTEAD OF A PACKAGE
 - Run time of the processing is the same, O(total lines): organisation does not change the
   algorithm.
 - One-time import cost of a package: Python finds and compiles/loads the package and each
   sub-module ONCE (using cached .pyc files), then keeps them in sys.modules; every later
   `import` is a dictionary lookup, O(1) (section 6: the second import takes microseconds).
   Cost = O(number of modules) for the first import. A package of 4 files costs a little
   more to start than one script (more file lookups), measured in a fraction of a
   millisecond; the memory is about the same (same code objects) plus a small overhead
   for each module object and its namespace.
 - Effort to find and change a function: single script = O(size of the file) scrolling /
   searching in one big file; package = O(1) look-ups by file name, then a search in a small file.
   The price is more files, and imports to keep consistent.
"""
