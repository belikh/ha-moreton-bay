"""Waste collection date helpers."""

from __future__ import annotations

from datetime import date, timedelta

_WEEKDAY_NAMES = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}

RECYCLE_WEEK_1 = "WEEK 1"
RECYCLE_WEEK_2 = "WEEK 2"


def normalise_weekday(bin_day: str) -> str | None:
    """Return the upper-cased weekday name, or None if unknown."""
    value = (bin_day or "").strip().upper()
    return value if value in _WEEKDAY_NAMES else None


def next_collection_date(
    bin_day: str,
    today: date,
) -> date | None:
    """Return the next date whose weekday matches *bin_day*.

    If today already matches, today is returned (collection today).
    """
    weekday = normalise_weekday(bin_day)
    if weekday is None:
        return None
    target = _WEEKDAY_NAMES[weekday]
    delta = (target - today.weekday()) % 7
    return today + timedelta(days=delta)


def is_recycle_week(
    recycle_week: str,
    on_date: date,
    epoch: date,
) -> bool:
    """Return whether *on_date* falls in WEEK 1 (recycle) or WEEK 2.

    Weeks alternate every seven days from *epoch*. WEEK 1 is recycle,
    WEEK 2 is garden organics, matching the council's two-week cycle.
    """
    value = (recycle_week or "").strip().upper()
    if value not in (RECYCLE_WEEK_1, RECYCLE_WEEK_2):
        return False
    weeks = (on_date - epoch).days // 7
    in_week_1 = weeks % 2 == 0
    return in_week_1 == (value == RECYCLE_WEEK_1)


def put_out_tonight(
    bin_day: str,
    on_date: date,
) -> bool:
    """Return True if bins go out tonight for a tomorrow collection."""
    return normalise_weekday(bin_day) is not None and (
        next_collection_date(bin_day, on_date + timedelta(days=1))
        == on_date + timedelta(days=1)
    )


EPOCH = date(2026, 1, 5)


def next_recycle_date(
    bin_day: str,
    recycle_week: str,
    today: date,
) -> date | None:
    """Return the next date where recycling is collected.

    General waste is weekly; recycling runs on the property's
    Recycle_Week (WEEK 1 or WEEK 2) in the fortnightly cycle
    anchored to EPOCH (Monday 2026-01-05 = WEEK 1).
    """
    nxt = next_collection_date(bin_day, today)
    if nxt is None:
        return None
    for _ in range(3):
        if is_recycle_week(recycle_week, nxt, EPOCH):
            return nxt
        nxt += timedelta(days=7)
    return nxt


def recycle_out_tonight(
    bin_day: str,
    recycle_week: str,
    on_date: date,
) -> bool:
    """Return True if the recycling bin goes out tonight."""
    return next_recycle_date(bin_day, recycle_week, on_date + timedelta(days=1)) == (
        on_date + timedelta(days=1)
    )


def collection_type(
    bin_day: str,
    recycle_week: str,
    on_date: date,
) -> str:
    """Return 'Recycling', 'Organics', or 'General only' for next collection."""
    nxt = next_collection_date(bin_day, on_date)
    if nxt is None:
        return "Unknown"
    return "Recycling" if is_recycle_week(recycle_week, nxt, EPOCH) else "Organics"
