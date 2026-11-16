"""Organisation (a): everything in ONE script."""
from pathlib import Path


def read_records(data_dir):
    """Read every daily file once. Returns ({register: {date: status}}, damaged_lines)."""
    records, damaged = {}, []
    for path in sorted(Path(data_dir).glob("*.txt")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, start=1):
                    parts = [x.strip() for x in line.strip().split(",")]
                    if line.strip() == "":
                        continue
                    if len(parts) != 3 or parts[2] not in ("P", "A"):
                        damaged.append((path.name, line_no))
                        continue
                    reg, date, status = parts
                    records.setdefault(reg, {})[date] = status
        except (OSError, UnicodeDecodeError):
            damaged.append((path.name, 0))
    return records, damaged


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


def format_report(rows, low, damaged):
    lines = [f"{'register':<12}{'present':>8}{'total':>7}{'percent':>9}"]
    lines += [f"{r[0]:<12}{r[1]:>8}{r[2]:>7}{r[3]:>9}" for r in rows]
    lines.append("below 75%: " + ", ".join(r[0] for r in low))
    lines.append(f"damaged lines: {len(damaged)}")
    return "\n".join(lines)


def format_absentees(regs):                                                # 5.2 NEW
    return "absent 3 consecutive days: " + (", ".join(regs) or "none")     # 5.2 NEW


def main():
    records, damaged = read_records(Path(__file__).resolve().parents[1] / "data")
    rows = compute_stats(records)
    print(format_report(rows, below_threshold(rows), damaged))
    print(format_absentees(three_day_absentees(records)))                  # 5.2 NEW


if __name__ == "__main__":
    main()
