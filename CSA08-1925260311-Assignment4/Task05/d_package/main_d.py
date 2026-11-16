"""Organisation (d): main script that uses the package attendance/."""
from pathlib import Path

import attendance                                  # runs attendance/__init__.py once

if __name__ == "__main__":
    records, damaged = attendance.read_records(Path(__file__).resolve().parents[1] / "data")
    rows = attendance.compute_stats(records)
    print(attendance.format_report(rows, attendance.below_threshold(rows), damaged))
    print(attendance.format_absentees(attendance.three_day_absentees(records)))   # 5.2 NEW
