from django.test import TestCase
from .services.hos_engine import plan_trip


class HOSEngineTests(TestCase):
    """
    These don't touch the database or the web layer at all - they call
    the engine directly with hand-picked numbers and check the output
    against what the FMCSA rules say should happen.
    """

    def test_short_trip_needs_no_rest(self):
        segments = plan_trip(
            leg1_miles=50, leg1_hours=1, leg2_miles=100, leg2_hours=2, cycle_hours_used=5
        )
        statuses = [s["status"] for s in segments]
        self.assertNotIn("off_duty", statuses)

    def test_long_trip_forces_a_rest(self):
        segments = plan_trip(
            leg1_miles=200, leg1_hours=3, leg2_miles=800, leg2_hours=13, cycle_hours_used=0
        )
        statuses = [s["status"] for s in segments]
        self.assertIn("off_duty", statuses)

    def test_fuel_stop_appears_past_1000_miles(self):
        segments = plan_trip(
            leg1_miles=0, leg1_hours=0, leg2_miles=1200, leg2_hours=20, cycle_hours_used=0
        )
        fuel_stops = [s for s in segments if s["label"] == "Fuel stop"]
        self.assertGreaterEqual(len(fuel_stops), 1)