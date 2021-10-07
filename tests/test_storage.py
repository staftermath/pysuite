import json

import pytest

from pysuite.storage import Storage
from tests.test_auth import storage_auth
from tests.helper import resource_folder


@pytest.fixture()
def storage(storage_auth):
    return Storage(service=storage_auth.get_service_client())


@pytest.mark.parametrize(
    ("gs_path", "raise_error", "expected_bucket", "expected_object"),
    [
        ["gs://my_bucket/ok", False, "my_bucket", "ok"],
        ["gs://another_bucket/my/object.txt", False, "another_bucket", "my/object.txt"],
        ["//my_bucket/ok", True, None, None],
        ["/tmp/ok", True, None, None],
    ]
)
def test_split_gs_object_return_correct_value_or_raise_error_correctly(storage, gs_path, raise_error, expected_bucket,
                                                                       expected_object):
    if raise_error:
        with pytest.raises(ValueError):
            storage._split_gs_object(gs_path)
    else:
        result_bucket, result_object = storage._split_gs_object(gs_path)
        assert result_bucket == expected_bucket
        assert result_object == expected_object
