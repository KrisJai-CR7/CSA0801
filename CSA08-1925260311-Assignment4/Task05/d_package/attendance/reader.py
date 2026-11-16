"""attendance.reader - reading files."""
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
