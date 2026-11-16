"""Organisation (c): statistics."""


def percentage(present, total):
    return round(100 * present / total, 2) if total else 0.0


def compute_stats(records):
    """[(register, present, total, percentage)] sorted by register number."""
    rows = []
    for reg in sorted(records):
        statuses = list(records[reg].values())
        present = statuses.count("P")
        rows.append((reg, present, len(statuses), percentage(present, len(statuses))))
    return rows


def below_threshold(rows, limit=75):
    return [r for r in rows if r[3] < limit]


def three_day_absentees(records, run=3):                                   # 5.2 NEW
    """Registers absent on `run` consecutive recorded days."""             # 5.2 NEW
    found = []                                                             # 5.2 NEW
    for reg in sorted(records):                                            # 5.2 NEW
        streak = 0                                                         # 5.2 NEW
        for date in sorted(records[reg]):                                  # 5.2 NEW
            streak = streak + 1 if records[reg][date] == "A" else 0        # 5.2 NEW
            if streak >= run:                                              # 5.2 NEW
                found.append(reg)                                          # 5.2 NEW
                break                                                      # 5.2 NEW
    return found                                                           # 5.2 NEW


if __name__ == "__main__":
    demo = {"1": {"d1": "A", "d2": "A", "d3": "A"}, "2": {"d1": "P", "d2": "A", "d3": "P"}}
    rows = compute_stats(demo)
    print("self-test:", rows, below_threshold(rows),
          three_day_absentees(demo))                                       # 5.2 NEW
