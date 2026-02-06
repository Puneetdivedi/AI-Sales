from datetime import datetime


def _stringify(value):
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def _truncate(text, max_width):
    if max_width is None:
        return text
    if len(text) <= max_width:
        return text
    if max_width <= 3:
        return text[:max_width]
    return text[: max_width - 3] + "..."


def print_table(rows, columns, title=None, max_width=None):
    """Print a simple table.

    columns: list of (key, label)
    rows: list of dicts
    """
    if title:
        print(title)

    if not rows:
        print("No data.")
        return

    widths = []
    for key, label in columns:
        width = len(label)
        for row in rows:
            cell = _truncate(_stringify(row.get(key, "")), max_width)
            width = max(width, len(cell))
        widths.append(width)

    header = " | ".join(label.ljust(widths[i]) for i, (_, label) in enumerate(columns))
    print(header)
    print("-" * len(header))

    for row in rows:
        line = " | ".join(
            _truncate(_stringify(row.get(key, "")), max_width).ljust(widths[i])
            for i, (key, _) in enumerate(columns)
        )
        print(line)


def print_kv(title, items):
    if title:
        print(title)
    for key, value in items:
        print(f"- {key}: {value}")


def pretty_money(value, currency="$"):
    try:
        return f"{currency}{float(value):.2f}"
    except (TypeError, ValueError):
        return f"{currency}0.00"


def now_date_label():
    return datetime.now().strftime("%Y-%m-%d")
