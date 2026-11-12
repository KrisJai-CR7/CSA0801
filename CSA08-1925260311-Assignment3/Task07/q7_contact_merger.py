"""
Q7 - Design a Contact-Merging Program from First Principles (10 Marks)

Stage 1 - INTERPRET THE PROBLEM (2 marks)
  Input  : contacts from several sources; each contact = {"name": str,
           "phones": [str...], "emails": [str...]} (fields may be missing)
  Output : a list of merged people, each with ONE display name, ALL names seen,
           a SET of normalised numbers and a SET of e-mails.
  Rule for "same person" (two contacts are the same person if they share at least
  one NORMALISED phone number or one NORMALISED e-mail). The name is NOT used to
  decide, because different people can have the same name and the same person can
  be written as "Dr. Ravi" and "ravi kumar". A contact with neither number nor
  e-mail is keyed by its normalised name (the only information available).
  Data structures: dict (key -> person id), set (numbers, e-mails, names: no
  duplicates), list (input and output), union-find parent list (to join
  groups that are linked later by a contact with two numbers).
  Measurable requirements:
    R1  "+91 98400 12345", "09840012345", "9840012345" give the same key.
    R2  every output person has no duplicate numbers/e-mails.
    R3  no number or e-mail occurs in two different output people.
    R4  two different people with the same name but different numbers stay separate.
    R5  merging n contacts takes O(n) average time (100,000 contacts in a few seconds).
    R6  missing fields do not crash the program.
"""
import random
import re
import time

TITLES = {"dr", "mr", "mrs", "ms", "prof", "shri", "smt", "mx"}


# ------------------------------------------------ Stage 2 - normalisation
def norm_phone(raw):
    """Keep digits; drop country code 91 or a leading trunk 0; keep last 10."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) > 10 and digits.startswith("91"):
        digits = digits[2:]
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    return digits if len(digits) == 10 else ""      # invalid -> ignored


def norm_email(raw):
    return (raw or "").strip().lower()


def norm_name(raw):
    """lower case, punctuation removed, titles removed, spaces collapsed."""
    words = re.sub(r"[^a-z\s]", " ", (raw or "").lower()).split()
    return " ".join(w for w in words if w not in TITLES)


# ------------------------------------------------ Stage 2 - the merge design
"""
PSEUDOCODE
    parent <- []                                  // union-find over contact ids
    owner  <- empty dict                          // key -> id of first contact seen with it
    for each contact c with id i:
        keys <- { "p:"+norm_phone(p) for p in c.phones } U { "e:"+norm_email(e) ... }
        if keys is empty and name present: keys <- { "n:"+norm_name(c.name) }
        parent[i] <- i
        for each key k in keys:
            if k in owner: union(i, owner[k])     // O(1) average dictionary lookup
            else:          owner[k] <- i
    people <- empty dict root -> {names:set, phones:set, emails:set}
    for each contact i: add its data to people[find(i)]
    return values of people
"""


def merge_contacts(contacts):
    parent = list(range(len(contacts)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]            # path compression
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    owner = {}
    cleaned = []
    for i, c in enumerate(contacts):
        phones = {p for p in map(norm_phone, c.get("phones", [])) if p}
        emails = {e for e in map(norm_email, c.get("emails", [])) if e}
        name = norm_name(c.get("name", ""))
        keys = {"p:" + p for p in phones} | {"e:" + e for e in emails}
        if not keys and name:
            keys = {"n:" + name}
        cleaned.append((name, phones, emails))
        for k in keys:
            if k in owner:
                union(i, owner[k])
            else:
                owner[k] = i

    people = {}
    for i, (name, phones, emails) in enumerate(cleaned):
        person = people.setdefault(find(i), {"names": set(), "phones": set(), "emails": set()})
        if name:
            person["names"].add(name)
        person["phones"] |= phones
        person["emails"] |= emails
    return list(people.values())


def merge_pairwise(contacts):
    """Alternative: compare EVERY pair of contacts: O(n^2) comparisons."""
    cleaned = []
    for c in contacts:
        phones = {p for p in map(norm_phone, c.get("phones", [])) if p}
        emails = {e for e in map(norm_email, c.get("emails", [])) if e}
        cleaned.append({"names": {norm_name(c.get("name", ""))} - {""},
                        "phones": phones, "emails": emails})
    people = []
    for c in cleaned:
        for p in people:
            if p["phones"] & c["phones"] or p["emails"] & c["emails"]:
                p["names"] |= c["names"]; p["phones"] |= c["phones"]; p["emails"] |= c["emails"]
                break
        else:
            people.append(c)
    # a second pass is needed when a later contact links two earlier people
    merged = True
    while merged:
        merged = False
        for i in range(len(people)):
            for j in range(i + 1, len(people)):
                a, b = people[i], people[j]
                if a["phones"] & b["phones"] or a["emails"] & b["emails"]:
                    a["names"] |= b["names"]; a["phones"] |= b["phones"]; a["emails"] |= b["emails"]
                    del people[j]
                    merged = True
                    break
            if merged:
                break
    return people


def show(people):
    for p in sorted(people, key=lambda p: sorted(p["names"])):
        print("  names:", sorted(p["names"]), "| phones:", sorted(p["phones"]),
              "| emails:", sorted(p["emails"]))


def canon(people):
    return sorted((sorted(p["names"]), sorted(p["phones"]), sorted(p["emails"])) for p in people)


def make_contacts(n, seed=0):
    """~n/2 distinct people; each appears in several formats and sources."""
    rnd = random.Random(seed)
    people = max(1, n // 2)
    contacts = []
    for _ in range(n):
        pid = rnd.randrange(people)
        num = 9000000000 + pid * 7919 % 999999999
        fmt = rnd.choice([f"+91 {str(num)[:5]} {str(num)[5:]}", f"0{num}", str(num),
                          f"+91-{num}"])
        c = {"name": rnd.choice([f"Dr. Person{pid}", f"person{pid} kumar", f"PERSON{pid}"]),
             "phones": [fmt]}
        if rnd.random() < 0.5:
            c["emails"] = [f"Person{pid}@Mail.com".upper() if rnd.random() < 0.5 else f"person{pid}@mail.com"]
        contacts.append(c)
    return contacts


if __name__ == "__main__":
    # ---------------------------------------------- Stage 3 - test cases
    contacts = [
        {"name": "Dr. Ravi",   "phones": ["+91 98400 12345"], "emails": ["ravi@mail.com"]},
        {"name": "ravi kumar", "phones": ["9840012345"]},                         # same number
        {"name": "Ravi K",     "emails": ["RAVI@mail.com", "r.k@work.org"]},     # same e-mail
        {"name": "Ravi",       "phones": ["98765 43210"]},                       # another Ravi
        {"name": "Meena",      "phones": ["09840012345"]},                       # dialled with 0 -> Ravi's number
        {"name": "Anita"},                                                        # no phone, no e-mail
        {"name": "anita",      "phones": []},                                     # same name only
        {"phones": ["+91 90000 11111"]},                                          # no name
        {"name": "Joe", "phones": ["12345"]},                                     # invalid number
    ]
    people = merge_contacts(contacts)
    print("MERGED RESULT")
    show(people)

    expected = [
        (["anita"], [], []),
        (["joe"], [], []),
        ([], ["9000011111"], []),
        (["meena", "ravi", "ravi k", "ravi kumar"], ["9840012345"], ["r.k@work.org", "ravi@mail.com"]),
        (["ravi"], ["9876543210"], []),
    ]
    got = canon(people)
    print("\nHAND-MERGED EXPECTATION")
    for e in expected:
        print(" ", e)
    print("matches the program:", got == sorted(expected))
    print("5 people from 9 contacts; the two 'Ravi' people with different numbers stay separate:",
          len(people) == 5)

    # R2 / R3 check on generated data
    big = make_contacts(1_000, seed=5)
    ppl = merge_contacts(big)
    all_numbers = [p for person in ppl for p in person["phones"]]
    print("\nR3 check (no number in two people):", len(all_numbers) == len(set(all_numbers)))

    # ---------------------------------------------- measurements
    print(f"\n{'contacts':>9} {'dictionary s':>13} {'pairwise s':>11} {'people':>8} same result")
    for n in (1_000, 100_000):
        data = make_contacts(n, seed=n)
        t0 = time.perf_counter(); r1 = merge_contacts(data); t1 = time.perf_counter() - t0
        if n <= 1_000:
            t0 = time.perf_counter(); r2 = merge_pairwise(data); t2 = time.perf_counter() - t0
            print(f"{n:>9,} {t1:>13.4f} {t2:>11.4f} {len(r1):>8,} {canon(r1) == canon(r2)}")
        else:
            # pairwise at 100,000 would need ~5 x 10^9 comparisons: extrapolate
            # from the measured 1,000-contact time (quadratic: x 10,000).
            print(f"{n:>9,} {t1:>13.4f} {'~' + format(t2 * 10_000, '.0f') + ' (est.)':>11} "
                  f"{len(r1):>8,} (pairwise not run)")


"""
Stage 4 - DEFEND THE DESIGN (2 marks)
 - Why a dictionary beats comparing every pair: comparing all pairs needs n(n-1)/2
   comparisons = O(n^2): 5,000 for 100 contacts but ~5 billion for 100,000.
   The dictionary maps each normalised key to its first owner, so a contact finds
   its duplicates with one O(1)-average lookup per key -> O(n) in total. Every
   contact is processed once, whatever the number of contacts.
 - Two different people with the same name: the name is not used as a key when a
   phone or e-mail exists, so "Ravi" 98400 12345 and "Ravi" 98765 43210 remain
   two separate people (R4). Their names are merged only if a number/e-mail is
   shared. Only a contact with NO number and NO e-mail is keyed by name (the best
   available information).
 - One remaining limitation: the rule "same number = same person" is wrong when
   people SHARE a number (a family landline, an office board number) - they would be
   merged wrongly; and the same person with completely different numbers and no
   shared e-mail (new SIM, no overlap) can never be matched. Name similarity
   ("Ravi K" vs "Ravi Kumar") would need fuzzy matching and a user's confirmation.

ALTERNATIVE CONCEPT & COMPLEXITY (n contacts)
 - Compare every pair: time O(n^2) (about n^2 / 2 set intersections), space O(n) for
   the cleaned contacts. Measured: 1,000 contacts take the time in the table;
   100,000 would take about 10,000x longer (quadratic) - impractical.
 - Dictionary / union-find: time O(n) on average (each contact does a few dictionary
   operations; union-find with path compression is almost constant, O(alpha(n))),
   space O(n) for the key dictionary and the parent array. Measured: 100,000
   contacts take the time shown in the table.
"""
