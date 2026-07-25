"""
Both geocoding.py and routing.py call out to free public servers that
occasionally hang or time out under load - not a bug in my code,
just what comes with free infrastructure. This retries a failed
request once before actually giving up, so a single slow response
doesn't crash the whole trip-planning request.
"""

import time
import requests


def get_with_retry(url, retries=2, backoff_seconds=1, **kwargs):
    """
    Same as requests.get(), but tries again once or twice before
    raising, since one slow response from a free public server
    shouldn't be enough to fail the entire request.
    """
    last_error = None
    for attempt in range(retries + 1):
        try:
            response = requests.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            last_error = e
            if attempt < retries:
                time.sleep(backoff_seconds)
    raise last_error