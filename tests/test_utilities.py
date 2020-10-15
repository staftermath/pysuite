import pytest

from googleapiclient.errors import HttpError

from pysuite.utilities import retry_on_out_of_quota, MAX_RETRY_ATTRIBUTE, SLEEP_ATTRIBUTE


class TestClass:

    def __init__(self, fail_times: int, max_retry: int, sleep: int):
        self.fail_times = fail_times
        setattr(self, MAX_RETRY_ATTRIBUTE, max_retry)
        setattr(self, SLEEP_ATTRIBUTE, sleep)


    @retry_on_out_of_quota()
    def foo(self, err_msg: str):
        error = b'{"error": {"message": "wow", "details": "dummy", }}'

        class DummyResponse:
            @property
            def reason(self):
                return err_msg

            @property
            def status(self):
                return 403

        reason = DummyResponse()

        while self.fail_times > 0:
            self.fail_times -= 1
            raise HttpError(reason, error)


@pytest.mark.parametrize("error_msg",
                         [
                             "oh User Rate Limit Exceeded wow",
                             "Quota exceeded what do we do"
                         ])
def test_retry_on_out_of_quota_retry_correctly(error_msg):
    test_class = TestClass(fail_times=2, max_retry=3, sleep=0.1)

    with pytest.warns(UserWarning) as record:
        test_class.foo(error_msg)

    assert len(record) == 2


@pytest.mark.parametrize("error_msg",
                         [
                             "oh User Rate Limit Exceeded wow",
                             "Quota exceeded what do we do"
                         ])
def test_retry_on_out_of_quota_max_retry_fewer_than_fail_time_raise_error_correctly(error_msg):
    test_class = TestClass(fail_times=2, max_retry=1, sleep=0.1)

    with pytest.raises(HttpError), pytest.warns(UserWarning) as record:
        test_class.foo(error_msg)

    assert len(record) == 1


def test_retry_on_out_of_quota_mismatch_error_raise_error_correctly():
    test_class = TestClass(fail_times=1, max_retry=2, sleep=0.1)

    with pytest.warns(None) as record, pytest.raises(HttpError):
        test_class.foo("mismatching error msg")

    assert len(record) == 0
