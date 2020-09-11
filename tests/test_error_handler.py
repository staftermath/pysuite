import logging

import pytest
from googleapiclient.errors import HttpError

from pysuite import Drive, Sheets
from pysuite.auth import ErrorHandler, handle_rate_exceeded_exception

from tests.test_auth import multi_auth


@pytest.mark.parametrize("msg",
                         [
                             ".*st m.*",
                             "^test",
                             ".*msg$"
                         ])
def test_handle_exception_correctly(msg, capsys):
    @ErrorHandler(exception=TypeError, pattern=msg, max_retry=3, sleep=0.1)
    def raise_exception(exception: Exception, msg: str):
        raise exception(msg)

    with pytest.raises(TypeError), pytest.warns(UserWarning, match="handled exception test msg. remaining retry: 0"):
        raise_exception(exception=TypeError, msg="test msg")


@pytest.mark.parametrize(("exception", "msg"),
                         [
                             (ValueError, "good msg"),  # mismatching exception type
                             (TypeError, "bad msg"), # mismatching msg value
                         ])
def test_handle_exception_raise_uncaught_exception_correctly(exception, msg, caplog):
    @ErrorHandler(exception=TypeError, pattern="good msg", max_retry=3)
    def raise_exception(exception: Exception, msg: str):
        raise exception(msg)

    with pytest.raises(exception), pytest.warns(UserWarning, match="good msg") as result:
        raise_exception(exception=exception, msg=msg)

    assert len(result) == 0


@pytest.mark.parametrize("class_name",
                         [
                             "Drive",
                             "Sheets"
                         ])
def test_quota_exceeded_retry_return_correct_class_type(class_name, multi_auth):
    expected = eval(class_name)
    result = expected(service=multi_auth.get_service_client(class_name.lower()))
    assert isinstance(result, expected)


@pytest.fixture()
def test_error_class():
    @handle_rate_exceeded_exception(sleep=0.1)
    class TestErrorClass:
        def raise_exception(self, exception: Exception):
            raise exception

    return TestErrorClass()


@pytest.mark.parametrize("msg",
                         [
                             "Wow User Rate Limit Exceeded",
                             "Quota exceeded"
                         ])
def test_handle_rate_exceeded_exception_gives_class_ability_to_handle_http_error_correctly(test_error_class, msg):
    error = b'{"error": {"message": "User Rate Limit Exceeded", "details": "dummy", }}'

    class DummyResponse:
        @property
        def reason(self):
            return msg

        @property
        def status(self):
            return 403

    reason = DummyResponse()

    with pytest.raises(HttpError), pytest.warns(UserWarning, match="remaining retry") as result:
        test_error_class.raise_exception(HttpError(reason, error))

    assert len(result) == 3
