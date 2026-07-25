"""
Takes the flat list of segments from the HOS engine and splits it
into per-day chunks - because a real driver's log book has one page
per calendar day, even when a rest period runs past midnight into the
next one.

It also guarantees every day's segments add up to a full 24 hours,
which the engine alone can't promise - the engine only records time
the driver is actively doing something, so the stretch before a
trip's very first activity (e.g. the hours before a 2pm start on day
1) would otherwise be missing entirely. This fills any such gap with
an implicit "off duty" block, matching the standard assumption for
unaccounted time on a driver's log.
"""

from datetime import datetime, timedelta


def split_into_daily_logs(segments):
    """
    Input: the flat segment list from hos_engine.plan_trip().
    Output: one entry per calendar day the trip touches, each with a
    gapless, full-24-hour segment list and hour totals - exactly what
    LogSheet needs to draw one accurate grid per day.
    """
    daily_logs = {}

    for segment in segments:
        start = datetime.fromisoformat(segment["start"])
        end = datetime.fromisoformat(segment["end"])

        # Walk this segment day by day in case it crosses midnight -
        # a segment running 10pm to 6am becomes two pieces: one ending
        # at midnight, one starting fresh the next morning.
        current = start
        while current < end:
            day_key = current.date().isoformat()
            midnight = datetime.combine(current.date() + timedelta(days=1), datetime.min.time())
            piece_end = min(end, midnight)

            if day_key not in daily_logs:
                daily_logs[day_key] = _new_day(day_key)

            _append_piece(daily_logs[day_key], segment["status"], current, piece_end, segment["label"])
            current = piece_end

    _pad_gaps_to_full_days(daily_logs)

    # Sorted by date, not just dict insertion order, so day 1 always
    # comes before day 2 no matter what.
    return [daily_logs[key] for key in sorted(daily_logs.keys())]


def _new_day(day_key):
    return {
        "date": day_key,
        "segments": [],
        "totals": {"driving": 0.0, "on_duty_not_driving": 0.0, "off_duty": 0.0},
    }


def _append_piece(day, status, start, end, label):
    hours = (end - start).total_seconds() / 3600
    day["segments"].append({
        "status": status,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "label": label,
    })
    day["totals"][status] += round(hours, 2)


def _pad_gaps_to_full_days(daily_logs):
    for day in daily_logs.values():
        day["segments"].sort(key=lambda s: s["start"])
        day_start = datetime.fromisoformat(day["date"])
        day_end = day_start + timedelta(days=1)
        cursor = day_start
        filled = []

        for segment in day["segments"]:
            seg_start = datetime.fromisoformat(segment["start"])
            if seg_start > cursor:
                filled.append(_gap_segment(cursor, seg_start))
                day["totals"]["off_duty"] += round((seg_start - cursor).total_seconds() / 3600, 2)
            filled.append(segment)
            cursor = datetime.fromisoformat(segment["end"])

        if cursor < day_end:
            filled.append(_gap_segment(cursor, day_end))
            day["totals"]["off_duty"] += round((day_end - cursor).total_seconds() / 3600, 2)

        day["segments"] = filled


def _gap_segment(start, end):
    return {"status": "off_duty", "start": start.isoformat(), "end": end.isoformat(), "label": "Off duty"}