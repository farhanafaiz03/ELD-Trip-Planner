

import requests
from .http_utils import get_with_retry

OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"


class RoutingError(Exception):
    """Raised when OSRM can't find, or can't be reached for, a route."""
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

    try:
        response = get_with_retry(url, params=params, timeout=20)
    except requests.exceptions.RequestException as e:
        raise RoutingError(f"Could not reach the routing service between {start} and {end}") from e

    data = response.json()
    if data.get("code") != "Ok" or not data.get("routes"):
        raise RoutingError(f"OSRM could not find a route between {start} and {end}")

    route = data["routes"][0]

    # Flip OSRM's [lon, lat] pairs to [lat, lon], since that's what
    # Leaflet (our map library) expects.
    geometry = [[lat, lon] for lon, lat in route["geometry"]["coordinates"]]

    return {
        "distance_miles": route["distance"] / 1609.34,
        "duration_hours": route["duration"] / 3600,
        "geometry": geometry,
    }