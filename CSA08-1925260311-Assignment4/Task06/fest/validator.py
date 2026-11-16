"""fest.validator - validation of ONE registration line using string methods only."""


class InvalidRecord(Exception):
    """A registration line cannot be accepted. `kind` says why (damaged / bad e-mail)."""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def is_valid_email(email):
    """Simple rule set (no regular expressions):
    no spaces; exactly one '@'; non-empty local part made of letters, digits and . _ - +;
    domain with at least one '.', no empty label ('..', leading or trailing '.'), and a
    last label of at least 2 letters."""
    if not email or " " in email or email.count("@") != 1:
        return False
    local, domain = email.split("@")
    if not local or not local.replace(".", "").replace("_", "").replace("-", "") \
            .replace("+", "").isalnum():
        return False
    labels = domain.split(".")
    if len(labels) < 2 or any(label == "" for label in labels):
        return False
    return all(label.replace("-", "").isalnum() for label in labels) \
        and labels[-1].isalpha() and len(labels[-1]) >= 2


def parse_registration(line):
    """'192311001,Arun,CSE,arun@mail.com,Dance;Quiz' ->
       {'regno','name','department','email','events'(set)}  or raises InvalidRecord."""
    parts = [p.strip() for p in line.strip().split(",")]
    if len(parts) != 5:
        raise InvalidRecord("damaged", f"expected 5 fields, found {len(parts)}")
    regno, name, department, email, events_text = parts
    if not (regno.isdigit() and len(regno) == 9):
        raise InvalidRecord("damaged", f"register number {regno!r} must be 9 digits")
    if not name or not department:
        raise InvalidRecord("damaged", "name or department is empty")
    events = {e.strip().title() for e in events_text.split(";") if e.strip()}
    if not events:
        raise InvalidRecord("damaged", "no events chosen")
    if not is_valid_email(email):
        raise InvalidRecord("bad e-mail", f"invalid e-mail {email!r}")
    return {"regno": regno, "name": name, "department": department.upper(),
            "email": email.lower(), "events": events}
