"""fest.writer - all output files (with statements, explicit encoding, mode "w")."""
import csv
from pathlib import Path


def slug(event):
    return event.lower().replace(" ", "_")


def write_master(out_dir, people):
    with open(Path(out_dir) / "master.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["regno", "name", "department", "email", "events"])
        for regno in sorted(people):
            p = people[regno]
            w.writerow([regno, p["name"], p["department"], p["email"],
                        ";".join(sorted(p["events"]))])


def write_event_lists(out_dir, people):
    events = {}
    for regno in sorted(people):
        for e in people[regno]["events"]:
            events.setdefault(e, []).append(regno)
    folder = Path(out_dir) / "events"
    folder.mkdir(exist_ok=True)
    for e, regs in events.items():
        with open(folder / f"{slug(e)}.txt", "w", encoding="utf-8") as f:
            for r in regs:
                f.write(f"{r},{people[r]['name']},{people[r]['department']}\n")
    return {e: len(r) for e, r in sorted(events.items())}


def write_error_log(out_dir, entries):
    with open(Path(out_dir) / "errors.log", "w", encoding="utf-8") as f:
        for source, line_no, kind, message, text in entries:
            where = f"{source}:{line_no}" if line_no else source
            f.write(f"{where}: {kind}: {message}" + (f": {text}" if text else "") + "\n")


def write_summary(out_dir, stats, per_event):
    lines = ["FEST REGISTRATION SUMMARY", "=" * 26,
             f"department files expected : {stats['files_expected']}",
             f"department files read     : {stats['files_read']}",
             f"department files missing  : {stats['files_problem']}",
             f"lines read                : {stats['lines']}",
             f"unique students (master)  : {stats['unique']}",
             f"duplicate registrations   : {stats['duplicates']} (events merged)",
             f"invalid e-mail addresses  : {stats['bad_email']}",
             f"damaged lines             : {stats['damaged']}",
             "", "students per department:"]
    lines += [f"  {d:<8}{n:>4}" for d, n in sorted(stats["per_department"].items())]
    lines += ["", "participants per event:"]
    lines += [f"  {e:<14}{n:>4}" for e, n in per_event.items()]
    with open(Path(out_dir) / "summary.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return "\n".join(lines)
