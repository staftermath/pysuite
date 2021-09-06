import json

import pytest

from pysuite.vision import Vision
from tests.test_auth import vision_auth
from tests.helper import resource_folder

test_image = resource_folder / "vision_test_image.jpg"

@pytest.fixture()
def vision(vision_auth):
    return Vision(service=vision_auth.get_service_client(), max_retry=5, sleep=10)


@pytest.mark.parametrize(
    ("methods", "expected_file"),
    [
        ["text_detection", resource_folder / "expected_text_detection.json"],
        [["text_detection"], resource_folder / "expected_text_detection.json"],
        [["text_detection", "label_detection"], resource_folder / "expected_two_type_detection.json"],
    ]
)
def test_vision_annotate_image_return_values_correctly(vision, methods, expected_file):
    result = vision.annotate_image(test_image, methods=methods)
    with open(expected_file, "r") as f:
        expected = json.load(f)
    assert Vision.to_json(result) == expected


def test_batch_annotate_image_return_values_correctly(vision):
    vision.add_request(image_path=test_image, methods="text_detection")
    vision.add_request(image_path=test_image, methods=["text_detection", "label_detection"])

    result = vision.batch_annotate_image()
    with open(resource_folder / "expected_batch_annotation.json", "r") as f:
        expected = json.load(f)

    assert Vision.to_json(result) == expected


@pytest.mark.skip("not implemented until GCS storage implementation")
def test_async_annotate_image_return_values_correctly(vision):
    vision.add_request(image_path=test_image, methods="text_detection")
    vision.add_request(image_path=test_image, methods=["text_detection", "label_detection"])

    result = vision.async_annotate_image()
    with open(resource_folder / "expected_batch_annotation.json", "r") as f:
        expected = json.load(f)

    assert Vision.to_json(result) == expected
