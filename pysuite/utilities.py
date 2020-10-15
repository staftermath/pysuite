import functools
import re
import warnings
import time

from googleapiclient.errors import HttpError

MAX_RETRY_ATTRIBUTE = "max_retry"
SLEEP_ATTRIBUTE = "sleep"


def retry_on_out_of_quota():
    def wrapper(method):
        @functools.wraps(wrapped=method)
        def wrapped_function(self, *args, **kwargs):
            max_retry = getattr(self, MAX_RETRY_ATTRIBUTE, 0)
            max_retry = max(max_retry, 0)
            sleep = getattr(self, SLEEP_ATTRIBUTE, 5)
            pattern = re.compile(".*(User Rate Limit Exceeded|Quota exceeded)+.*")
            while max_retry >= 0:
                try:
                    result = method(self, *args, **kwargs)
                    return result
                except HttpError as e:
                    if pattern.match(str(e)):
                        max_retry -= 1
                        warnings.warn(f"handled exception {e}. remaining retry: {max_retry}", UserWarning)
                        time.sleep(sleep)
                        sleep = sleep**2
                        continue

                    raise e

        return wrapped_function

    return wrapper
