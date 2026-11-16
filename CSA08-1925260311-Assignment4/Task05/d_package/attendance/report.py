"""attendance.report - writing reports."""


def format_report(rows, low, damaged):
    lines = [f"{'register':<12}{'present':>8}{'total':>7}{'percent':>9}"]
    lines += [f"{r[0]:<12}{r[1]:>8}{r[2]:>7}{r[3]:>9}" for r in rows]
    lines.append("below 75%: " + ", ".join(r[0] for r in low))
    lines.append(f"damaged lines: {len(damaged)}")
    return "\n".join(lines)


def format_absentees(regs):                                                # 5.2 NEW
    return "absent 3 consecutive days: " + (", ".join(regs) or "none")     # 5.2 NEW
