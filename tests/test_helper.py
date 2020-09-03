import pytest
from tests.helper import random_string


@pytest.mark.parametrize(("length", "expected"),
                         [
                             (2, "dr"),
                             (8, "drfXArgc")
                         ])
def test_random_string_return_result_correctly(length, expected):
    result = random_string(length, seed=123)
    assert result == expected
