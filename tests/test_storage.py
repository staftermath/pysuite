from pathlib import Path

import pytest

from google.cloud.storage.client import Bucket
from google.api_core.exceptions import NotFound

from pysuite.storage import Storage, _add_folder_tree_to_new_base_dir
from tests.test_auth import storage_auth
from tests.helper import resource_folder

TEST_BUCKET = "pysuite_bucket"


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


@pytest.fixture()
def prepare_env(storage):

    def purge():
        try:
            storage.remove_bucket(TEST_BUCKET, force=True)
        except:
            pass

    purge()
    yield
    purge()


def test_create_bucket_and_delete_bucket_and_get_bucket_execute_correctly(storage, prepare_env):
    with pytest.raises(NotFound):  # test bucket should not exist to begin with
        storage.get_bucket(TEST_BUCKET)

    result = storage.create_bucket(TEST_BUCKET)
    assert isinstance(result, Bucket)

    result = storage.get_bucket(TEST_BUCKET)
    assert isinstance(result, Bucket)

    storage.remove_bucket(TEST_BUCKET)

    with pytest.raises(NotFound):  # test bucket should now be removed
        storage.get_bucket(TEST_BUCKET)


@pytest.fixture()
def prepare_files(storage, tmpdir):
    base_dir = Path(tmpdir.mkdir("storage_test_files"))
    layer_1_dir = base_dir / "layer1"
    layer_1_dir.mkdir()
    for f in ["a.txt", "b.txt"]:
        with open(layer_1_dir / f, "w") as f:
            f.write(f"test {f}.")

    (base_dir / "base.txt").touch()
    return base_dir


def test_add_folder_tree_to_new_base_dir_return_value_correctly(prepare_files):
    result = list(_add_folder_tree_to_new_base_dir(prepare_files, "dummy_location/test"))
    expected = [
        (prepare_files / 'layer1', 'dummy_location/test/layer1'),
        (prepare_files / 'base.txt', 'dummy_location/test/base.txt'),
        (prepare_files / 'layer1' / 'b.txt', 'dummy_location/test/layer1/b.txt'),
        (prepare_files / 'layer1' / 'a.txt', 'dummy_location/test/layer1/a.txt')
    ]
    assert result == expected


@pytest.fixture()
def create_bucket(storage, prepare_env):
    storage.create_bucket(TEST_BUCKET)


def test_upload_and_download_file_create_files_correctly(storage, create_bucket, prepare_files, tmpdir):
    target_gs_object = f"gs://{TEST_BUCKET}/test"
    from_object = prepare_files
    storage.upload(from_object=from_object, to_object=target_gs_object)

    downloaded_dir = Path(tmpdir.mkdir("downloaded"))
    storage.download(from_object=target_gs_object, to_object=downloaded_dir)

    result = list(downloaded_dir.rglob("*"))
    expected = [
        downloaded_dir / 'test',
        downloaded_dir / 'test' / 'layer1',
        downloaded_dir / 'test' / 'base.txt',
        downloaded_dir / 'test' / 'layer1' / 'b.txt',
        downloaded_dir / 'test' / 'layer1' / 'a.txt'
    ]
    assert result == expected


@pytest.fixture()
def upload_file(storage, create_bucket, prepare_files):
    target_gs_object = f"gs://{TEST_BUCKET}/test"
    storage.upload(from_object=prepare_files, to_object=target_gs_object)
    return target_gs_object


def test_list_return_values_correctly(storage, upload_file):
    gs_object = upload_file
    iterator = storage.list(target_object=gs_object)
    result = [blob.name for blob in iterator]
    expected = ['test/base.txt', 'test/layer1/a.txt', 'test/layer1/b.txt']
    assert result == expected
