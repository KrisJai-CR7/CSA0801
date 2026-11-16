"""fest.reader - reading a department file. A file problem is reported, never raised."""


def read_lines(path):
    """Return (list of (line_number, text), problem). Exactly one of them is empty/None.
    Handles a missing file, permission problems, a folder instead of a file and bad encoding."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [(n, line.rstrip("\n")) for n, line in enumerate(f, start=1)
                    if line.strip()], None
    except FileNotFoundError:
        return [], "department file is missing"
    except PermissionError:
        return [], "permission denied"
    except IsADirectoryError:
        return [], "path is a folder, not a file"
    except UnicodeDecodeError as e:
        return [], f"file is not valid UTF-8 ({e.reason})"
    except OSError as e:
        return [], f"cannot be read ({e})"
