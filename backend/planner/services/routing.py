"""
routing.py

Given two (latitude, longitude) points, asks OSRM's free public
routing server for the real driving distance, driving time, and the
actual road-following route line between them - the same kind of
information a GPS app would give you. No API key required.

Uses OSRM's public demo server (router.project-osrm.org) - fine for
this assessment's traffic level, not meant for high-volume production.
"""

import requests

OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"


class RoutingError(Exception):
    """Raised when OSRM can't find or return a route."""
    pass


def get_route(start, end):
    """
    start / end are (latitude, longitude) tuples.
    Returns {"distance_miles": float, "duration_hours": float, "geometry": [[lat, lon], ...]}
    """
    start_lat, start_lon = start
    end_lat, end_lon = end

    # OSRM wants coordinates as "lon,lat" - backwards from how we
    # normally say them out loud. Easy mistake, worth the comment.
    coords = f"{start_lon},{start_lat};{end_lon},{end_lat}"
    url = f"{OSRM_BASE_URL}/{coords}"

    params = {
        "overview": "full",       # full route line, not a simplified one
        "geometries": "geojson",  # coordinates as plain [lon, lat] pairs
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()

    data = response.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RoutingError(f"OSRM could not find a route between {start} and {end}")

    route = data["routes"][0]

    # Flip OSRM's [lon, lat] pairs to [lat, lon], since that's what
    # Leaflet (our map library, in Module 6) expects.
    geometry = [[lat, lon] for lon, lat in route["geometry"]["coordinates"]]

    return {
        "distance_miles": route["distance"] / 1609.34,
        "duration_hours": route["duration"] / 3600,
        "geometry": geometry,
    }