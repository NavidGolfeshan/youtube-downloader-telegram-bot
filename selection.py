"""Playlist track-selection parsing, isolated for easy testing."""

import re


def parse_track_selection(text: str, total: int) -> list[int]:
    text = text.strip().lower()
    if text == "all":
        return list(range(total))
    if not text:
        raise ValueError("Please enter `all` or at least one track number.")

    selected: set[int] = set()
    for part in re.split(r"[,;\s]+", text):
        if not part:
            continue
        if "-" in part:
            left, right = part.split("-", 1)
            if not left.isdigit() or not right.isdigit():
                raise ValueError(f"Invalid range: {part}")
            start, end = int(left), int(right)
            if start > end:
                start, end = end, start
            if start < 1 or end > total:
                raise ValueError(f"Range {part} is outside the valid range 1-{total}.")
            selected.update(range(start - 1, end))
        else:
            if not part.isdigit():
                raise ValueError(f"Invalid selection: {part}")
            number = int(part)
            if not 1 <= number <= total:
                raise ValueError(f"Track {number} is outside the valid range 1-{total}.")
            selected.add(number - 1)

    if not selected:
        raise ValueError("No tracks selected.")
    return sorted(selected)

