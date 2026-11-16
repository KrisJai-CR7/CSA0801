"""fest.processor - controls the run. It must NEVER stop because of one bad line or file."""
from pathlib import Path

from . import reader, validator, writer


def run_pipeline(input_dir, output_dir, departments):
    """Process the file <dept>.txt for every department. Returns (people, stats, errors)."""
    input_dir, output_dir = Path(input_dir), Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    people, seen, errors = {}, set(), []           # seen: set of register numbers (O(1) test)
    stats = {"files_expected": len(departments), "files_read": 0, "files_problem": 0,
             "lines": 0, "duplicates": 0, "bad_email": 0, "damaged": 0,
             "unique": 0, "per_department": {}}

    for dept in departments:
        source = f"{dept}.txt"
        lines, problem = reader.read_lines(input_dir / source)
        if problem:                                      # missing file etc.: log and go on
            errors.append((source, 0, "file problem", problem, ""))
            stats["files_problem"] += 1
            continue
        stats["files_read"] += 1
        for line_no, text in lines:
            stats["lines"] += 1
            try:
                rec = validator.parse_registration(text)
            except validator.InvalidRecord as e:          # expected: bad line
                key = "bad_email" if e.kind == "bad e-mail" else "damaged"
                stats[key] += 1
                errors.append((source, line_no, e.kind, str(e), text))
                continue
            except Exception as e:                        # last-resort boundary: RECORD it
                stats["damaged"] += 1                      # (never `pass`) and keep going
                errors.append((source, line_no, "unexpected error",
                               f"{type(e).__name__}: {e}", text))
                continue
            if rec["regno"] in seen:                      # duplicate registration
                extra = rec["events"] - people[rec["regno"]]["events"]
                people[rec["regno"]]["events"] |= rec["events"]
                stats["duplicates"] += 1
                errors.append((source, line_no, "duplicate", "already registered; events merged"
                               + (f" (added: {', '.join(sorted(extra))})" if extra else ""), text))
            else:
                seen.add(rec["regno"])
                people[rec["regno"]] = rec

    stats["unique"] = len(people)
    for p in people.values():
        stats["per_department"][p["department"]] = stats["per_department"].get(p["department"], 0) + 1
    writer.write_master(output_dir, people)
    per_event = writer.write_event_lists(output_dir, people)
    writer.write_error_log(output_dir, errors)
    summary = writer.write_summary(output_dir, stats, per_event)
    return people, stats, errors, summary
