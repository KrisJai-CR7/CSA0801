"""Organisation (c): main script; reader.py, stats.py and report.py sit in the same folder."""
from pathlib import Path

import reader
import report
import stats

if __name__ == "__main__":
    records, damaged = reader.read_records(Path(__file__).resolve().parents[1] / "data")
    rows = stats.compute_stats(records)
    print(report.format_report(rows, stats.below_threshold(rows), damaged))
    print(report.format_absentees(stats.three_day_absentees(records)))     # 5.2 NEW
