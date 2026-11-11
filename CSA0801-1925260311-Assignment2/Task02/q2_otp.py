"""
Q2 - Loops that Count Attempts (OTP verification at a bank kiosk)
3 wrong attempts -> account locked for 30 minutes. A blank entry is NOT an attempt.
Customer input is simulated with a list so the program runs unattended.
"""

CORRECT_OTP = "482910"
SECURITY_ANSWER = "chennai"


def make_reader(entries):
    """Return a function that gives the next simulated keyboard entry."""
    it = iter(entries)
    return lambda prompt="": next(it, None)       # None = no more input


# -------------------------------------------------- 1. while-loop version
def verify_while(read, max_attempts=3):
    attempts = 0
    entry = None
    while attempts < max_attempts:
        entry = read("Enter OTP: ")
        if entry is None:                          # kiosk timeout, stop cleanly
            print("  (no more input)")
            return "ABORTED"
        entry = entry.strip()
        if entry == "":
            print("  blank entry - not counted")
            continue                               # CONTINUE: skip counting
        if entry == CORRECT_OTP:
            print("  OTP accepted")
            break                                  # BREAK: success, leave loop
        attempts += 1                              # counter updated ONLY here
        left = max_attempts - attempts
        print(f"  wrong OTP, {left} attempt(s) left")
        if left == 0:
            pass                                   # PASS: placeholder - the lock
                                                   # is applied by the else clause
    else:
        # else runs only when the loop ended WITHOUT break
        print("  ACCOUNT LOCKED FOR 30 MINUTES")
        return "LOCKED"
    return "OK"


# ------------------------------------------- 2. for + range(3) version
def verify_for(read):
    for attempt in range(3):
        while True:                                # blank entries never use up
            entry = read("Enter OTP: ")            # an attempt of the for loop
            if entry is None:
                print("  (no more input)")
                return "ABORTED"
            if entry.strip() != "":
                break
            print("  blank entry - not counted")
        if entry.strip() == CORRECT_OTP:
            print("  OTP accepted")
            break
        print(f"  wrong OTP (attempt {attempt + 1} of 3)")
    else:
        print("  ACCOUNT LOCKED FOR 30 MINUTES")
        return "LOCKED"
    return "OK"


# ------------------------------------------------ changed condition
def verify_with_security_question(read):
    """
    Two extra attempts if the customer answers the security question correctly.
    The bonus can be earned only ONCE, so the limit becomes a variable that
    can grow. That is why a fixed `for range(3)` is no longer suitable and
    the while loop is the natural design.
    """
    max_attempts = 3
    bonus_given = False
    attempts = 0
    while attempts < max_attempts:
        entry = read("Enter OTP: ")
        if entry is None:
            return "ABORTED"
        entry = entry.strip()
        if entry == "":
            continue
        if entry == CORRECT_OTP:
            print("  OTP accepted")
            return "OK"
        attempts += 1
        print(f"  wrong OTP ({attempts}/{max_attempts})")
        if attempts == 3 and not bonus_given:      # all normal attempts used
            answer = read("Security answer: ")
            if answer and answer.strip().lower() == SECURITY_ANSWER:
                max_attempts += 2
                bonus_given = True
                print("  security answer correct: 2 extra attempts")
    print("  ACCOUNT LOCKED FOR 30 MINUTES")
    return "LOCKED"


# ----------------------------------------- alternative: recursion
def verify_recursive(read, attempt=1, max_attempts=3):
    if attempt > max_attempts:
        print("  ACCOUNT LOCKED FOR 30 MINUTES")
        return "LOCKED"
    entry = read("Enter OTP: ")
    if entry is None:
        return "ABORTED"
    if entry.strip() == "":
        return verify_recursive(read, attempt, max_attempts)   # not counted
    if entry.strip() == CORRECT_OTP:
        print("  OTP accepted")
        return "OK"
    print(f"  wrong OTP (attempt {attempt})")
    return verify_recursive(read, attempt + 1, max_attempts)


def run(title, func, entries, **kw):
    print(f"\n{title}\n  input: {entries}")
    print("  result:", func(make_reader(entries), **kw))


if __name__ == "__main__":
    scenarios = {
        "correct on 2nd try, with a blank": ["", "111111", CORRECT_OTP],
        "three wrong -> lock": ["1", "2", "3"],
        "blanks never count": ["", "", "", "1", "2", "3"],
    }
    for name, entries in scenarios.items():
        run("WHILE   | " + name, verify_while, entries)
    for name, entries in scenarios.items():
        run("FOR     | " + name, verify_for, entries)
    for name, entries in scenarios.items():
        run("RECURSE | " + name, verify_recursive, entries)

    run("CHANGED CONDITION | bonus earned, success on 5th",
        verify_with_security_question,
        ["1", "2", "3", "chennai", "4", CORRECT_OTP])
    run("CHANGED CONDITION | wrong security answer -> lock",
        verify_with_security_question,
        ["1", "2", "3", "mumbai"])
    run("CHANGED CONDITION | bonus earned but all 5 wrong -> lock",
        verify_with_security_question,
        ["1", "2", "3", "chennai", "4", "5"])


"""
ANSWERS
 - When is while more natural than for?  When the NUMBER OF ITERATIONS is not
   known in advance or differs from the number of loop passes: blank entries do
   not count, and the bonus can raise the limit. `while attempts < max` states
   "keep going while attempts remain". `for range(3)` is natural only when
   exactly 3 passes are always wanted.
 - Bug if the counter is updated in the wrong place: if attempts += 1 is placed
   at the top of the loop, a blank entry (even a correct one) uses up an
   attempt, so a customer can be locked out by blank Enter presses. If it is
   skipped on a path that loops again, the loop never ends (infinite loop).
 - break / continue / pass: break leaves the loop on success (and prevents the
   else clause from running); continue skips counting for a blank entry; pass
   is a do-nothing placeholder where a statement is syntactically required.
 - Loop else: executes only if the loop finished without break, exactly the
   "all attempts used up" situation, so the lock lives there.

ALTERNATIVE CONCEPT: recursion (verify_recursive)
 - Time O(a) for a attempts, in all versions.
 - Stack space: O(a) for recursion (one frame per attempt, and blank entries
   add frames too) versus O(1) for a loop. With a = 3 this is harmless, but
   recursion has no advantage here and would hit the recursion limit for a
   very long run of blank entries.
"""
