"""Organisation (b): main script that imports the module."""
from pathlib import Path

import attendance_lib as lib

if __name__ == "__main__":
    records, damaged = lib.read_records(Path(__file__).resolve().parents[1] / "data")
    rows = lib.compute_stats(records)
    print(lib.format_report(rows, lib.below_threshold(rows), damaged))
    print(lib.format_absentees(lib.three_day_absentees(records)))           # 5.2 NEW
