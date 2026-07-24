"""

This is the core logic of the app - the "brain". Given the distance
and driving time for the two legs of a trip (current -> pickup,
pickup -> dropoff), and how many hours of the 70-hour/8-day cycle the
driver has already used, this simulates the whole trip and returns an
ordered list of duty-status blocks: driving, on-duty-not-driving
(fuel/loading), and off-duty (breaks/rests).

Everything else in the app - the map stops, the drawn log sheets - is
just a different view of the list this file produces. If a number
looks wrong anywhere in the app, this is the file to check first.

Why cycle hours are tracked as a single running counter instead of a
true rolling 8-day window: the app only receives ONE number from the
driver ("hours already used"), not a day-by-day history, so there's
no way to reconstruct a true rolling window. A running counter that
resets to zero on a valid 34-hour restart is the correct, defensible
simplification given what the inputs actually give us.
"""

from datetime import datetime, timedelta

# ---- HOS rule constants, all sourced from the FMCSA guide ----
MAX_DRIVING_HOURS_PER_SHIFT = 11        # 11-hour driving limit
MAX_ON_DUTY_WINDOW_HOURS = 14           # 14-hour driving window
BREAK_REQUIRED_AFTER_HOURS = 8          # 30-min break after 8 cumulative driving hrs
BREAK_DURATION_HOURS = 0.5
MIN_OFF_DUTY_HOURS = 10                 # required rest between shifts
MAX_CYCLE_HOURS = 70                    # 70-hour/8-day on-duty ceiling
RESTART_HOURS = 34                      # 34-hour restart resets the cycle
FUEL_STOP_INTERVAL_MILES = 1000
FUEL_STOP_DURATION_HOURS = 0.5
PICKUP_DROPOFF_DURATION_HOURS = 1.0


class TripSimulator:
    """
    Walks through a trip in hour-sized chunks, applying HOS rules, and
    records every duty-status change as a "segment" - the same shape
    the frontend later uses to draw both the map stops and the log
    sheet grids.
    """

    def __init__(self, cycle_hours_used, start_time=None):
        # Hours of the 70-hour cycle already burned before this trip
        self.cycle_hours_used = cycle_hours_used

        # Clock starts "now" unless given a specific time - this only
        # affects what the log sheets say the date/time is, not the
        # HOS math itself.
        self.current_time = start_time or datetime.now().replace(
            minute=0, second=0, microsecond=0
        )

        # Counters that reset whenever the driver takes 10+ hours off
        self.shift_driving_hours = 0.0
        self.shift_on_duty_hours = 0.0
        self.hours_since_last_break = 0.0

        # Only resets on an actual fuel stop, not on rests - distance
        # driven doesn't disappear just because you slept.
        self.miles_since_fuel = 0.0

        # The actual output - the single source of truth for the app
        self.segments = []

    def _add_segment(self, status, hours, label, miles=0):
        """
        Every status change in the whole trip funnels through this
        one method, so the counters above never drift out of sync
        with the segment list.
        """
        if hours <= 0:
            return  # skip zero-length segments (e.g. a 0-mile leg)

        start = self.current_time
        end = self.current_time + timedelta(hours=hours)

        self.segments.append({
            "status": status,  # "driving" | "on_duty_not_driving" | "off_duty"
            "start": start.isoformat(),
            "end": end.isoformat(),
            "label": label,
            "miles": round(miles, 1),
        })

        self.current_time = end

        if status == "driving":
            self.shift_driving_hours += hours
            self.shift_on_duty_hours += hours
            self.hours_since_last_break += hours
            self.cycle_hours_used += hours
            self.miles_since_fuel += miles
        elif status == "on_duty_not_driving":
            self.shift_on_duty_hours += hours
            self.cycle_hours_used += hours
            # A break, fuel stop, or loading stop all count as "not
            # driving" - which is exactly what satisfies the 30-min
            # break requirement per the FMCSA guide.
            self.hours_since_last_break = 0.0
        elif status == "off_duty":
            # A full rest wipes every shift-level counter.
            self.shift_driving_hours = 0.0
            self.shift_on_duty_hours = 0.0
            self.hours_since_last_break = 0.0
            if hours >= RESTART_HOURS:
                # Only a valid 34-hour restart also wipes the cycle.
                self.cycle_hours_used = 0.0

    def drive_leg(self, total_miles, total_hours, leg_label):
        """
        Drives `total_miles` over `total_hours`, stopping to insert
        breaks, rests, and fuel stops exactly where the rules require.
        """
        miles_per_hour = total_miles / total_hours if total_hours else 0
        remaining_hours = total_hours

        while remaining_hours > 0:
            # Before driving another minute, check whether the
            # 70-hour cycle is already maxed out - force a restart
            # before anything else if so.
            if self.cycle_hours_used >= MAX_CYCLE_HOURS:
                self._add_segment(
                    "off_duty", RESTART_HOURS,
                    "34-hour restart (70-hour cycle limit reached)",
                )

            hours_left_in_driving_limit = MAX_DRIVING_HOURS_PER_SHIFT - self.shift_driving_hours
            hours_left_in_window = MAX_ON_DUTY_WINDOW_HOURS - self.shift_on_duty_hours
            hours_left_before_break = BREAK_REQUIRED_AFTER_HOURS - self.hours_since_last_break

            # Whichever limit runs out first is the binding constraint
            # on how much we're allowed to drive right now.
            chunk_hours = min(
                remaining_hours,
                hours_left_in_driving_limit,
                hours_left_in_window,
                hours_left_before_break,
            )

            if chunk_hours <= 0:
                # No legal driving time left - figure out which limit
                # hit zero and handle it. A maxed-out 11hr or 14hr
                # limit always needs a full 10-hour rest; only a
                # maxed-out break timer needs just the 30-minute break.
                if hours_left_in_driving_limit <= 0 or hours_left_in_window <= 0:
                    self._add_segment(
                        "off_duty", MIN_OFF_DUTY_HOURS, "Required 10-hour rest"
                    )
                else:
                    self._add_segment(
                        "on_duty_not_driving", BREAK_DURATION_HOURS,
                        "Required 30-minute break",
                    )
                continue  # re-check all limits fresh on the next pass

            # Respect the fuel-stop interval mid-drive: if this chunk
            # would cross the next 1000-mile mark, shorten it so we
            # stop exactly at that mileage instead of overshooting.
            chunk_miles = chunk_hours * miles_per_hour
            miles_to_next_fuel = FUEL_STOP_INTERVAL_MILES - self.miles_since_fuel
            if chunk_miles > miles_to_next_fuel > 0:
                chunk_hours = miles_to_next_fuel / miles_per_hour
                chunk_miles = miles_to_next_fuel

            self._add_segment("driving", chunk_hours, f"Driving - {leg_label}", chunk_miles)
            remaining_hours -= chunk_hours

            if self.miles_since_fuel >= FUEL_STOP_INTERVAL_MILES and remaining_hours > 0:
                self._add_segment("on_duty_not_driving", FUEL_STOP_DURATION_HOURS, "Fuel stop")
                self.miles_since_fuel = 0.0

    def add_stop(self, label, hours=PICKUP_DROPOFF_DURATION_HOURS):
        """Used for the 1-hour pickup / dropoff on-duty blocks."""
        self._add_segment("on_duty_not_driving", hours, label)


def plan_trip(leg1_miles, leg1_hours, leg2_miles, leg2_hours, cycle_hours_used, start_time=None):
    """
    Public entry point the Django view calls. Wraps TripSimulator so
    the rest of the app never needs to know how the simulation works
    internally - it just calls this one function and gets a list back.
    """
    sim = TripSimulator(cycle_hours_used=cycle_hours_used, start_time=start_time)

    sim.drive_leg(leg1_miles, leg1_hours, "to pickup")
    sim.add_stop("Loading at pickup")
    sim.drive_leg(leg2_miles, leg2_hours, "to dropoff")
    sim.add_stop("Unloading at dropoff")

    return sim.segments