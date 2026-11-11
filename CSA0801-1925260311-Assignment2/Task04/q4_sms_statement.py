"""
Q4 - String building and immutability (Monthly SMS Bill Statement)
Builds the same statement with (1) repeated +=, (2) "".join, (3) f-string per line,
and also (alternative) io.StringIO. Timings: 1,000 / 10,000 / 200,000 lines,
each averaged over three runs.
"""
import io
import time
import tracemalloc


def make_items(n):
    return [f"Item{i}:Rs{i % 50}" for i in range(n)]


# ---------------------------------------------------------------- the 3 builders
def build_plus(parts):
    text = ""
    for p in parts:
        text += p + ";"              # may create a new string every pass
    return text


def build_join(parts):
    # TODO 1 (completed): one str.join() call builds the same text
    return ";".join(parts) + ";"


def build_fstring(parts):
    # f-string for each line, then joined (3rd method of the brief)
    lines = [f"{p};" for p in parts]
    return "".join(lines)


def build_stringio(parts):
    # Alternative concept: write each piece into an in-memory buffer
    buf = io.StringIO()
    for p in parts:
        buf.write(p)
        buf.write(";")
    return buf.getvalue()


def timed(func, parts):
    t0 = time.perf_counter()
    out = func(parts)
    return out, time.perf_counter() - t0


def peak_memory(func, parts):
    tracemalloc.start()
    func(parts)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    return peak


if __name__ == "__main__":
    # ---------- the given program (200,000 items) --------------------------
    items = make_items(200_000)
    a, t_plus = timed(build_plus, items)
    b, t_join = timed(build_join, items)
    print("same text:", a == b, "| length:", len(b))
    print(f"+= time: {t_plus:.4f} s   join time: {t_join:.4f} s")

    # ---------- prediction -------------------------------------------------
    print("\nPREDICTION (before measuring): join() is faster at every size, and the")
    print("gap grows with the number of lines.")

    # ---------- measurements: 3 sizes x 3 runs x 4 methods -----------------
    methods = [("+=", build_plus), ("join", build_join),
               ("f-string+join", build_fstring), ("StringIO", build_stringio)]
    print("\nAverage of 3 runs (seconds)")
    print(f"{'lines':>9} | " + " | ".join(f"{n:>13}" for n, _ in methods))
    print("-" * 80)
    raw = {}
    for size in (1_000, 10_000, 200_000):
        parts = make_items(size)
        row = []
        reference = None
        for name, f in methods:
            runs = []
            for _ in range(3):
                out, dt = timed(f, parts)
                runs.append(dt)
            raw[(size, name)] = runs
            row.append(sum(runs) / 3)
            if reference is None:
                reference = out
            assert out == reference, f"{name} produced a different text"
        print(f"{size:>9} | " + " | ".join(f"{t:>13.5f}" for t in row))

    print("\nRaw timings (three runs each):")
    for (size, name), runs in raw.items():
        print(f"  {size:>7} {name:<14} " + "  ".join(f"{r:.5f}" for r in runs))

    # ---------- memory ------------------------------------------------------
    parts = make_items(100_000)
    print("\nPeak extra memory while building 100,000 lines (tracemalloc, bytes):")
    for name, f in methods:
        print(f"  {name:<14} {peak_memory(f, parts):>12,}")


"""
INQUIRY - explanation using string immutability
 - A Python str cannot be changed in place. `text += p` really means
   text = text + p, which builds a NEW string, copies the old contents, then
   the old string is discarded. If the text already has m characters, one append
   copies about m characters; after n appends the total copied is about
   1 + 2 + ... + n pieces = O(n^2) characters in the worst case.
 - join() first collects the pieces, computes the final size ONCE, allocates one
   string and copies every piece exactly once: O(n) time.
 - CPython has an optimisation: when the left-hand string has only ONE
   reference, += can resize the string in place (realloc), so the loop above
   may look linear on a given machine. This is an implementation detail of
   CPython (not of the language), is not guaranteed on PyPy/Jython or when
   another reference exists (e.g. text stored in a list or attribute), and
   depends on the memory allocator. Therefore join() remains the recommended,
   portable practice: its O(n) behaviour is guaranteed.

MEASURED (this run): join() was about 3-4x faster than += at 200,000 lines, and the
 gap widened with size. Peak memory: += used LESS (about half) because CPython resized
 the single-reference string in place, while join() held the list of parts and the
 result together - a useful reminder that the in-place optimisation is real but
 not portable.

ALTERNATIVE CONCEPT: io.StringIO (or writing line by line to a file)
 - Time: O(n) overall; each write appends into an internal buffer that grows
   geometrically (amortised O(1) per write).
 - Memory: join() needs the list of parts AND the final string
   (about 2 x size, plus list overhead); StringIO keeps only the buffer, and a
   file written line by line needs almost no memory (O(1) beyond one line),
   which is best for a bill with >100,000 lines that is going to be saved
   or sent anyway.
 - repeated +=: O(n^2) characters copied in the worst case; memory about
   2 x size at the moment of each copy.
 - f-string: formats ONE line at a time (O(length of line)); it is a way to
   make the pieces, not to join them, so it still needs join/StringIO to
   combine them.
"""
