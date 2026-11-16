"""Package attendance: reader, stats and report sub-modules."""
from .reader import read_records
from .report import format_absentees, format_report                       # 5.2 NEW
from .stats import (below_threshold, compute_stats, percentage,
                    three_day_absentees)                                   # 5.2 NEW

__all__ = ["read_records", "compute_stats", "below_threshold", "percentage",
           "three_day_absentees", "format_report", "format_absentees"]     # 5.2 NEW
