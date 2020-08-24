import pytest
from pathlib import Path

from pysuite.drive import Drive
from googleapiclient.errors import HttpError
from tests.test_auth import drive_client


@pytest.fixture()
def drive(drive_client):
    return Drive(client=drive_client.get_client())

def test_get_id_return_correct_value(drive):
    result = drive.get_id("drive_test_file")
    expected = "1-zIfn0kUcK6KI9PfZLXu6uCt01ZSOTOZ"
    assert result == expected


def test_get_id_for_non_unique_name_raise_runtime_error(drive):
    with pytest.raises(RuntimeError):
        drive.get_id("drive_test_non_unique_file")


def test_get_id_in_parent_id_return_correct_value(drive):
    result = drive.get_id("drive_test_non_unique_file", parent_id="1qcfrD7RqZWwPVO9C7tbL1PNRa2aUQlF8")
    expected = "12K7eoK6M3MNOcNQmfMFjL1mCz8A_-St8"
    assert result == expected


def test_download_create_file_correctly(drive, tmpdir):
    download_file = Path(tmpdir.join("test_download.txt"))
    drive.download(id="1-zIfn0kUcK6KI9PfZLXu6uCt01ZSOTOZ",
                   to_file=download_file)

    with open(download_file, 'r') as f:
        result = [l.strip() for l in f.readlines()]

    assert result == ["hello", "world"]


def test_upload_and_delete_correctly_create_and_remove_file(drive, tmpdir):
    file_to_upload = Path(tmpdir.join("test_upload_file"))
    file_to_upload.write_text("hello world")

    id = drive.upload(from_file=file_to_upload, name="test_file", parent_ids=["1_p0khJ5euUDbZhWiXbN5fefozKMD28yZ"])

    download_file = Path(tmpdir.join("test_downloaded_file"))
    drive.download(id=id, to_file=download_file)

    with open(download_file, 'r') as f:
        result = [l.strip() for l in f.readlines()]

    assert result == ["hello world"]

    drive.delete(id=id)

    with pytest.raises(HttpError):
        drive.download(id=id, to_file=download_file)


@pytest.fixture()
def clean_up_file(drive, tmpdir):
    file_to_upload = Path(tmpdir.join("test_upload_file"))
    file_to_upload.write_text("hello world")
    id = drive.upload(from_file=file_to_upload, name="temporary_drive_test_file")

    yield id

    drive.delete(id)


def test_update_change_file_content_correctly(drive, clean_up_file, tmpdir):
    file_to_update = Path(tmpdir.join("test_upload_file"))
    file_to_update.write_text("the world has changed")
    id = clean_up_file
    drive.update(id=id, from_file=file_to_update)

    downloaded_file = Path(tmpdir.join("test_update_file_downloaded"))
    drive.download(id=id, to_file=downloaded_file)
    with open(downloaded_file, 'r') as f:
        result = [l.strip() for l in f.readlines()]

    assert result == ["the world has changed"]
