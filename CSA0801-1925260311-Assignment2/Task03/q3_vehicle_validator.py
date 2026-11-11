"""
Q3 - Engineer a Vehicle Registration Number Validator (string operations, NO
regex in the solution; a regex version is shown only for the comparison).

Valid form: 2 letters (state) + 2 digits (district) + 1 or 2 letters (series)
            + 4 digits (number)    e.g.  TN09AB1234
"""
import re
import time


def normalise(text):
    """'tn 09 ab 1234' -> 'TN09AB1234' (spaces and hyphens removed, upper case)."""
    return text.replace(" ", "").replace("-", "").upper()


def is_valid(reg):
    """Valid form: 2 letters, 2 digits, 1 or 2 letters, 4 digits."""
    if len(reg) not in (9, 10):
        return False
    series_len = len(reg) - 8                    # 1 or 2 series letters
    return (reg[:2].isalpha()                    # state
            and reg[2:4].isdigit()               # district
            and reg[4:4 + series_len].isalpha()  # series
            and reg[-4:].isdigit())              # number


def format_reg(reg):
    """'TN09AB1234' -> 'TN 09 AB 1234' (call only for a valid number)."""
    return " ".join([reg[:2], reg[2:4], reg[4:-4], reg[-4:]])


def is_valid_regex(reg):
    return re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}", reg) is not None


# ------------------------------------------------------------- PREDICTIONS
# (raw input, predicted normalised value, predicted validity) written first
PREDICTIONS = [
    ("tn 09 ab 1234", "TN09AB1234", True),
    ("KA-01-M-0007", "KA01M0007", True),
    ("TN9AB1234", "TN9AB1234", False),         # 1-digit district -> '9A' not digits
    ("TN 22 1234 AB", "TN221234AB", False),    # series after the number
    ("mh-12-abc-1234", "MH12ABC1234", False),  # 3 series letters -> length 11
    ("t1 09 ab 1234", "T109AB1234", False),    # digit inside the state code
]

if __name__ == "__main__":
    print("--- Given test (TODO 1 and 2 completed) ---")
    for raw in ["tn 09 ab 1234", "KA-01-M-0007", "TN9AB1234", "TN 22 1234 AB"]:
        reg = normalise(raw)
        print(f"{raw:15} -> {reg:11} {'valid' if is_valid(reg) else 'INVALID'}")

    print("\n--- Six predicted inputs vs observed (4 invalid) ---")
    for raw, p_norm, p_ok in PREDICTIONS:
        reg = normalise(raw)
        ok = is_valid(reg)
        match = (reg == p_norm and ok == p_ok)
        shown = format_reg(reg) if ok else "-"
        print(f"{raw:16} norm={reg:12} valid={str(ok):5} fmt={shown:15} "
              f"prediction {'OK' if match else 'WRONG'}")

    print("\n--- Formatted valid numbers ---")
    for raw in ["tn 09 ab 1234", "KA-01-M-0007"]:
        print(f"{raw:15} -> {format_reg(normalise(raw))}")

    print("\n--- Slicing / immutability ---")
    text = "tn 09 ab 1234"
    up = text.upper()
    print("text.upper():", up, "| text still:", text)
    nine, ten = "TN09A1234", "TN09AB1234"
    print("s[-4:]  9-char:", nine[-4:], "| 10-char:", ten[-4:])
    print("s[4:-4] 9-char:", repr(nine[4:-4]), "| 10-char:", repr(ten[4:-4]))
    try:
        text[0] = "T"
    except TypeError as e:
        print("text[0] = 'T' ->", type(e).__name__ + ":", e)

    print("\n--- Slicing vs regex ---")
    samples = [normalise(r) for r, _, _ in PREDICTIONS] + ["TN09AB1234"] * 5
    print("agree on samples:", all(is_valid(s) == is_valid_regex(s) for s in samples))
    N = 200_000
    for name, f in (("slicing", is_valid), ("regex  ", is_valid_regex)):
        t0 = time.perf_counter()
        for _ in range(N):
            f("TN09AB1234")
        print(f"{name}: {time.perf_counter() - t0:.4f} s for {N} validations")


"""
INQUIRY ANSWERS
1. Why are strings immutable?  A str's characters cannot be changed in place.
   Immutability lets Python hash strings (use them as dict keys), share/intern
   them safely, and avoid accidental changes through other references. Every
   "modification" builds a NEW string.
2. text.upper() does not modify `text` because it returns a new string; the
   original object cannot change. Keep the result: text = text.upper().
3. s[-4:] is the last four characters; for BOTH a 9-char and a 10-char number
   it returns the 4-digit registration number. s[4:-4] is what lies between the
   district and the number: the series letters (1 letter for 9 chars, 2 for 10).
   Slicing from the END makes the same code work for both lengths.

ALTERNATIVE: regular expression  re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}", reg)
 - Time: both approaches are O(L) for a number of length L (each character is
   examined a constant number of times; this pattern has no nested quantifiers,
   so no backtracking blow-up). Slicing creates a few short substrings (O(L)
   copying); the regex engine adds fixed overhead per call. Space O(L) / O(1).
 - Readability: the regex states the whole format in one line and is easier to
   change (e.g. allow 3 series letters = {1,3}). The slicing version needs index
   arithmetic (len(reg) - 8, reg[-4:]) edited in several places, but needs no
   extra concept and is easy to step through.
 - Measured: see the timings above.
"""
