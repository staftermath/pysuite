import json
from pathlib import Path

import pytest

from pysuite.vision import Vision
from tests.test_auth import auth_fixture
from tests.test_storage import storage, prepare_env, create_bucket, prefix_lower, tmp_bucket
from tests.helper import resource_folder

test_image = resource_folder / "vision_test_image.jpg"


@pytest.fixture()
def vision(auth_fixture):
    return Vision(auth=auth_fixture)


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


def test_vision_to_json_when_input_type_incorrect_raise_exception_correctly():
    with pytest.raises(TypeError):
        Vision.to_json("random object")


def test_add_request_when_method_not_implemented_raise_exception_correctly(vision):
    with pytest.raises(NotImplementedError):
        vision.add_request(image_path=test_image, methods="Non existent method")


@pytest.mark.parametrize(
    "add_request",
    [True, False]
)
def test_batch_annotate_image_return_values_correctly(vision, add_request):
    if add_request:
        vision.add_request(image_path=test_image, methods="text_detection")
        vision.add_request(image_path=test_image, methods=["text_detection", "label_detection"])
        with open(resource_folder / "expected_batch_annotation.json", "r") as f:
            expected = json.load(f)
        response = vision.batch_annotate_image()
        result = Vision.to_json(response)

        assert result == expected
    else:
        with pytest.warns(UserWarning) as w:
            result = vision.batch_annotate_image()
            assert result is None
            result_warning = str(w.list[0].message)
            assert result_warning == "No requests was prepared"


@pytest.fixture()
def prepare_asycn_image_env(storage, create_bucket):
    gcs_test_image = f"gs://{create_bucket}/test_image.jpg"
    storage.upload(from_object=test_image, to_object=gcs_test_image)
    return gcs_test_image, create_bucket


def test_async_annotate_image_return_values_correctly(vision, prepare_asycn_image_env, storage, tmpdir):
    gcs_test_image, bucket = prepare_asycn_image_env
    output_path = "test_pysuite_vision"
    output_gcs_uri = f"gs://{bucket}/{output_path}/"
    vision.add_request(image_path=gcs_test_image, methods="text_detection")
    vision.add_request(image_path=gcs_test_image, methods=["text_detection", "label_detection"])

    operation = vision.async_annotate_image(output_gcs_uri=output_gcs_uri, batch_size=1)
    # waiting for operation to complete
    response = operation.result()

    output_dir = Path(tmpdir.mkdir("test_vision_async"))
    storage.download(from_object=response.output_config.gcs_destination.uri, to_object=output_dir)
    result_created_files = sorted((output_dir / output_path).rglob("*"))
    file_names_on_gcs = ["output-1-to-1.json", "output-2-to-2.json"]
    expected_files = [output_dir / output_path / f for f in file_names_on_gcs]
    assert result_created_files == expected_files, "created output file list incorrect."

    for file in file_names_on_gcs:
        with open(resource_folder / f"test_vision_{file}", "r") as expected_f, \
             open(output_dir / output_path / file) as result_f:
            expected_json = json.load(expected_f)
            # the bucket is randomly generated for parallel execution, hence must be assigned to expected every time
            expected_json['responses'][0]['context']['uri'] = gcs_test_image
            result_json = json.load(result_f)
            assert result_json == expected_json, "created output file content incorrect."


def test_async_annotate_image_when_no_request_is_added_return_values_correctly(vision, caplog):
    with pytest.warns(UserWarning) as w:
        result = vision.async_annotate_image(output_gcs_uri="gs://bucket_not_exist/no_output_needed/", batch_size=2)
        assert result is None
        result_warning = str(w.list[0].message)
        assert result_warning == "No requests was prepared"
