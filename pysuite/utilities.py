import functools
import re
import warnings
import time

from googleapiclient.errors import HttpError

MAX_RETRY_ATTRIBUTE = "max_retry"
SLEEP_ATTRIBUTE = "sleep"


def retry_on_out_of_quota():
    """A decorator to give wrapped function ability to retry on quota exceeded related HttpError raise by Google API.
    It only works on class method and requires "max_retry" and "sleep" attribute in the class. If `max_retry` is
    non-positive, no retry will be attempt. `sleep` is the base number of seconds between consecutive retries. The number
    of wait seconds will double after each sleep.

    :return:
    """
    def wrapper(method):
        @functools.wraps(wrapped=method)
        def wrapped_function(self, *args, **kwargs):
            max_retry = getattr(self, MAX_RETRY_ATTRIBUTE, 0)
            max_retry = max(max_retry, 0)
            sleep = getattr(self, SLEEP_ATTRIBUTE, 5)
            if sleep < 0:
                raise AttributeError(f"{SLEEP_ATTRIBUTE} must be positive. Got {sleep}")

            pattern = re.compile(".*(User Rate Limit Exceeded|Quota exceeded)+.*")
            while True:
                max_retry -= 1
                try:
                    result = method(self, *args, **kwargs)
                    return result
                except HttpError as e:
                    if max_retry >= 0 and pattern.match(str(e)):
                        warnings.warn(f"handled exception {e}. remaining retry: {max_retry}", UserWarning)
                        time.sleep(sleep)
                        sleep = sleep*2
                        continue

                    raise e

        return wrapped_function

    return wrapper
