import logging
import pytest

from pysuite import Drive, Sheets
from pysuite.auth import ErrorHandler

from tests.test_auth import multi_auth


@pytest.fixture(scope="module")
def reset_logging():
    logger = logging.getLogger("ErrorHandler")
    logger.setLevel("DEBUG")
    yield
    logger.setLevel("WARNING")


@pytest.mark.parametrize("msg",
                         [
                             ".*st m.*",
                             "^test",
                             ".*msg$"
                         ])
def test_handle_exception_correctly(reset_logging, msg, caplog):
    @ErrorHandler(exception=TypeError, pattern=msg, max_retry=3, sleep=0.1)
    def raise_exception(exception: Exception, msg: str):
        raise exception(msg)

    raise_exception(exception=TypeError, msg="test msg")

    result = caplog.messages
    expected = [f'handled exception test msg. remaining retry: {count}' for count in range(2, -1, -1)]
    assert result == expected


@pytest.mark.parametrize(("exception", "msg"),
                         [
                             (ValueError, "good msg"),  # mismatching exception type
                             (TypeError, "bad msg"), # mismatching msg value
                         ])
def test_handle_exception_raise_uncaught_exception_correctly(reset_logging, exception, msg, caplog):
    @ErrorHandler(exception=TypeError, pattern="good msg", max_retry=3)
    def raise_exception(exception: Exception, msg: str):
        raise exception(msg)

    with pytest.raises(exception):
        raise_exception(exception=exception, msg=msg)

    result = caplog.messages
    assert f'handled exception good msg. remaining retry: 2' not in result


@pytest.mark.parametrize("class_name",
                         [
                             "Drive",
                             "Sheets"
                         ])
def test_quota_exceeded_retry_return_correct_class_type(class_name, multi_auth):
    expected = eval(class_name)
    result = expected(service=multi_auth.get_service_client(class_name.lower()))
    assert isinstance(result, expected)
