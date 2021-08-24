import json

import pytest

from pysuite.vision import Vision
from tests.test_auth import vision_auth
from tests.helper import resource_folder

test_image = resource_folder / "wakeupcat.jpg"

@pytest.fixture()
def vision(vision_auth):
    return Vision(service=vision_auth.get_service_client(), max_retry=5, sleep=10)


@pytest.mark.parametrize(
    ("method", "expected_file"),
    [
        ["text_detection", resource_folder / "expected_wakeupcat_text_detection.json"]
    ]
)
def test_vision_annotate_image_return_values_correctly(vision, method, expected_file):
    result = vision.annotate_image(test_image, method=method)
    with open(expected_file, "r") as f:
        expected = json.load(f)

    assert result == expected
