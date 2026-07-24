"""
views.py

The one API endpoint the frontend talks to. Its job is purely to wire
together pieces we already built and tested separately - it has no
HOS logic of its own, on purpose, so the actual rules stay easy to
test in isolation over in hos_engine.py.

Flow: validate input -> geocode 3 addresses -> get 2 driving routes ->
run the HOS simulation -> split into daily pages -> hand back one
JSON response with everything the frontend needs.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import TripRequestSerializer
from .services.geocoding import geocode_address, GeocodingError
from .services.routing import get_route, RoutingError
from .services.hos_engine import plan_trip
from .services.daily_logs import split_into_daily_logs


class PlanTripView(APIView):
    def post(self, request):
        serializer = TripRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        try:
            current_coords = geocode_address(data["current_location"])
            pickup_coords = geocode_address(data["pickup_location"])
            dropoff_coords = geocode_address(data["dropoff_location"])
        except GeocodingError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            leg1 = get_route(current_coords, pickup_coords)
            leg2 = get_route(pickup_coords, dropoff_coords)
        except RoutingError as e:
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        # This is the one call that actually does the thinking -
        # everything above just gathered its inputs, everything below
        # just reformats its output for the frontend.
        segments = plan_trip(
            leg1_miles=leg1["distance_miles"],
            leg1_hours=leg1["duration_hours"],
            leg2_miles=leg2["distance_miles"],
            leg2_hours=leg2["duration_hours"],
            cycle_hours_used=data["cycle_hours_used"],
        )

        daily_logs = split_into_daily_logs(segments)

        total_distance = leg1["distance_miles"] + leg2["distance_miles"]
        combined_geometry = leg1["geometry"] + leg2["geometry"]

        stops = [
            {"type": "pickup", "lat": pickup_coords[0], "lng": pickup_coords[1], "label": "Pickup"},
            {"type": "dropoff", "lat": dropoff_coords[0], "lng": dropoff_coords[1], "label": "Dropoff"},
        ]

        # For every non-driving stop the engine inserted (rest, break,
        # fuel), estimate roughly where along the route it happens by
        # matching how many miles have been driven so far to the same
        # fraction of the way along the route line. Not pixel-perfect,
        # but close enough to be genuinely useful on the map.
        cumulative_miles = 0.0
        for segment in segments:
            if segment["status"] == "driving":
                cumulative_miles += segment["miles"]
            else:
                fraction = min(cumulative_miles / total_distance, 1.0) if total_distance else 0
                index = int(fraction * (len(combined_geometry) - 1))
                lat, lng = combined_geometry[index]
                stops.append({
                    "type": segment["status"],
                    "lat": lat,
                    "lng": lng,
                    "label": segment["label"],
                })

        return Response({
            "route": {
                "geometry": combined_geometry,
                "distance_miles": round(total_distance, 1),
                "duration_hours": round(leg1["duration_hours"] + leg2["duration_hours"], 1),
            },
            "stops": stops,
            "daily_logs": daily_logs,
        })