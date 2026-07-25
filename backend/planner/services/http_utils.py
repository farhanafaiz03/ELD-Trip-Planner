

import time
import requests


def get_with_retry(url, retries=1, backoff_seconds=1, **kwargs):
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