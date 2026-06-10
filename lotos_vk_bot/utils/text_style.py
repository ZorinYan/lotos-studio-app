DIVIDER = "━━━━━━━━━━━━━━━"
LIGHT = "─ ─ ─ ─ ─ ─ ─ ─"
INDENT = "    "

CIRCLED = ("①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩")


def marker(index: int) -> str:
    if 1 <= index <= len(CIRCLED):
        return CIRCLED[index - 1]
    return f"{index}."


def page_header(emoji: str, title: str) -> str:
    return f"{emoji}  {title}\n{DIVIDER}"


def section(emoji: str, title: str) -> str:
    return f"\n{emoji}  {title}\n{LIGHT}"


def join_blocks(blocks: list[str], *, gap: str = LIGHT) -> str:
    if not blocks:
        return ""
    return f"\n{gap}\n".join(blocks)


def join_lines(blocks: list[str]) -> str:
    return "\n\n".join(blocks)


def spots_line(capacity: int, booked: int) -> str | None:
    if capacity <= 0:
        return None
    free = max(capacity - booked, 0)
    if free == 0:
        return "🔴  мест нет"
    return f"🟢  свободно {free} из {capacity}"


def format_class_block(
    time_str: str,
    title: str,
    trainer: str,
    *,
    capacity: int = 0,
    booked: int = 0,
) -> str:
    lines = [f"🕐  {time_str}  ·  {title}", f"👤  {trainer}"]
    spots = spots_line(capacity, booked)
    if spots:
        lines.append(spots)
    return "\n".join(lines)


def format_record_block(
    index: int,
    when: str,
    service: str,
    trainer: str,
    *,
    extra: str | None = None,
) -> str:
    lines = [
        f"{marker(index)}  {when}",
        f"{INDENT}{service}",
        f"{INDENT}👤  {trainer}",
    ]
    if extra:
        lines.append(f"{INDENT}{extra}")
    return "\n".join(lines)

