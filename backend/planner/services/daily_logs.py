"""
daily_logs.py

Takes the flat list of segments from the HOS engine and splits it
into per-day chunks - because a real driver's log book has one page
per calendar day, even when a rest period runs past midnight into the
next one. This is the file that makes "one sheet per day" work.
"""

from datetime import datetime, timedelta


def split_into_daily_logs(segments):
    """
    Input: the flat segment list from hos_engine.plan_trip().
    Output: one entry per calendar day the trip touches, each with
    its own segments and hour totals - exactly what LogSheet (Module 7)
    will need to draw one grid per day.
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
                daily_logs[day_key] = {
                    "date": day_key,
                    "segments": [],
                    "totals": {"driving": 0.0, "on_duty_not_driving": 0.0, "off_duty": 0.0},
                }

            hours = (piece_end - current).total_seconds() / 3600
            daily_logs[day_key]["segments"].append({
                "status": segment["status"],
                "start": current.isoformat(),
                "end": piece_end.isoformat(),
                "label": segment["label"],
            })
            daily_logs[day_key]["totals"][segment["status"]] += round(hours, 2)

            current = piece_end

    # Sorted by date, not just dict insertion order, so day 1 always
    # comes before day 2 no matter what.
    return [daily_logs[key] for key in sorted(daily_logs.keys())]