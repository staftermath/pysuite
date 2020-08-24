import pytest

from pysuite.drive import Drive
from tests.test_auth import drive_client


@pytest.fixture()
def drive(drive_client):
    return Drive(client=drive_client.get_client())

def test_drive_get_id_return_correct_value(drive):
    result = drive.get_id("drive_test_file")
    expected = "1-zIfn0kUcK6KI9PfZLXu6uCt01ZSOTOZ"
    assert result == expected


def test_drive_get_id_for_non_unique_name_raise_runtime_error(drive):
    with pytest.raises(RuntimeError):
        drive.get_id("drive_test_non_unique_file")


def test_drive_get_id_in_parent_id_return_correct_value(drive):
    result = drive.get_id("drive_test_non_unique_file", parent_id="1qcfrD7RqZWwPVO9C7tbL1PNRa2aUQlF8")
    expected = "12K7eoK6M3MNOcNQmfMFjL1mCz8A_-St8"
    assert result == expected
