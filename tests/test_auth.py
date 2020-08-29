import pytest
from pathlib import Path
import json

from googleapiclient.discovery import Resource

from pysuite.auth import Authentication


credential_folder = Path(".").resolve().parent / "credentials"
credential_file = credential_folder / "credential.json"
drive_token_file = credential_folder / "drive_token.json"
sheet_token_file = credential_folder / "sheet_token.json"


@pytest.mark.skip("this will prompt browser")
def test_load_from_file_correctly(tmpdir):
    token_path = Path(tmpdir.join("test_load_from_file_token.json"))
    result = Authentication(credential=credential_file, token=token_path, service="drive")
    assert result._credential.valid
    assert not result._credential.expired


def test_when_token_not_exists_and_service_is_none_raise_exception(tmpdir):
    with pytest.raises(ValueError):
        Authentication(credential=credential_file, token=Path(tmpdir.join("not_exist.json")))


@pytest.mark.parametrize(
    ("token_dict"),
    [
        {"token": "aaa", "missing_refresh_token": "bbb", "service": "drive"},  # need "refresh_token" key
        {"missing_token": "aaa", "refresh_token": "bbb", "service": "drive"},  # need "token" key
    ]
)
def test_when_credential_file_has_incorrect_format_raise_exception(tmpdir, token_dict):
    temp_token_file = Path(tmpdir.join("temp_token.json"))
    with open(temp_token_file, 'w') as f:
        json.dump(token_dict, f)

    with pytest.raises(KeyError):
        Authentication(token=temp_token_file, service="drive")


@pytest.fixture()
def drive_auth():
    return Authentication(token=drive_token_file, service="drive")


def test_get_client_no_service_provided_return_correct_values(drive_auth):
    result = drive_auth.get_service()
    assert isinstance(result, Resource)


@pytest.fixture()
def sheet_auth():
    return Authentication(token=sheet_token_file, service="sheets")


def test_get_client_service_authorized_return_correct_values(sheet_auth):
    result = sheet_auth.get_service()
    assert isinstance(result, Resource)
