"""
geocoding.py

Turns a human-typed address string ("Chicago, IL") into a
(latitude, longitude) pair, using OpenStreetMap's free Nominatim
geocoding service. Both the routing service and the map on the
frontend need real coordinates, not text - this file makes that
translation.

Nominatim's usage policy requires a descriptive User-Agent header -
this is required, not optional, or requests get silently rejected.
"""

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "spotter-eld-planner (assessment project)"}


class GeocodingError(Exception):
    """Raised when an address can't be turned into coordinates."""
    pass


def geocode_address(address):
    """
    Given an address string, returns (latitude, longitude).
    Raises GeocodingError if the address can't be found.
    """
    params = {"q": address, "format": "json", "limit": 1}

    response = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=10)
    response.raise_for_status()  # raises if Nominatim itself errors

    results = response.json()
    if not results:
        raise GeocodingError(f"Could not find a location for: {address}")

    first_result = results[0]
    return float(first_result["lat"]), float(first_result["lon"])