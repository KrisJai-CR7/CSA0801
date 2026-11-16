"""Package fest - College Fest Registration Desk.

reader.py     reads one department file line by line (never stops on a file problem)
validator.py  checks one line: fields, register number, e-mail (string methods only)
writer.py     writes master.csv, event lists, summary.txt and errors.log
processor.py  controls the whole run: read -> validate -> de-duplicate -> write
"""
from .processor import run_pipeline
from .validator import InvalidRecord, is_valid_email, parse_registration

__all__ = ["run_pipeline", "InvalidRecord", "is_valid_email", "parse_registration"]
