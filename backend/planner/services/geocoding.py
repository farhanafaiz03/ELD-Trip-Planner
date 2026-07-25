

import requests
from .http_utils import get_with_retry

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
HEADERS = {"User-Agent": "spotter-eld-planner (assessment project)"}


class GeocodingError(Exception):
    """Raised when an address can't be turned into coordinates."""
    pass


def geocode_address(address):
    """
    Given an address string, returns (latitude, longitude).
    Raises GeocodingError if the address can't be found or the
    geocoding service can't be reached at all.
    """
    params = {"q": address, "format": "json", "limit": 1}

    try:
        response = get_with_retry(NOMINATIM_URL, params=params, headers=HEADERS, timeout=15)
    except requests.exceptions.RequestException as e:
        # Catches timeouts, connection errors, bad status codes - any
        # of these mean "couldn't get an answer", which the rest of
        # the app should treat the same way as "address not found".
        raise GeocodingError(f"Could not reach the geocoding service for: {address}") from e

    results = response.json()
    if not results:
        raise GeocodingError(f"Could not find a location for: {address}")

    first_result = results[0]
    return float(first_result["lat"]), float(first_result["lon"])