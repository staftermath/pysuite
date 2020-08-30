import pytest
from pathlib import Path
import json

from googleapiclient.discovery import Resource

from pysuite.auth import Authentication


credential_folder = Path(".").resolve().parent / "credentials"
credential_file = credential_folder / "credential.json"
drive_token_file = credential_folder / "drive_token.json"
sheet_token_file = credential_folder / "sheets_token.json"


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
def test_when_token_file_has_incorrect_format_raise_exception(tmpdir, token_dict):
    temp_token_file = Path(tmpdir.join("temp_token.json"))
    with open(temp_token_file, 'w') as f:
        json.dump(token_dict, f)

    with pytest.raises(KeyError):
        Authentication(credential=credential_file, token=temp_token_file, service="drive")


@pytest.mark.parametrize(
    ("credential_dict"),
    [
        {"missing_installed": {"irrelevant": "a"}},  # need "installed" key
        {"installed": {"missing_token_uri": "a", "client_id": "b", "client_secret": "c"}},  # need "token_uri" key
        {"installed": {"token_uri": "a", "missing_client_id": "b", "client_secret": "c"}},  # need "client_id" key
        {"installed": {"token_uri": "a", "client_id": "b", "missing_client_secret": "c"}},  # need "client_secret" key
    ]
)
def test_when_credential_file_has_incorrect_format_raise_exception(tmpdir, credential_dict):
    temp_credential_file = Path(tmpdir.join("temp_credential.json"))
    with open(temp_credential_file, 'w') as f:
        json.dump(credential_dict, f)

    with pytest.raises(KeyError):
        Authentication(credential=temp_credential_file, token=drive_token_file, service="drive")


@pytest.fixture()
def drive_auth():
    return Authentication(credential=credential_file, token=drive_token_file, service="drive")


def test_get_client_no_service_provided_return_correct_values(drive_auth):
    result = drive_auth.get_service()
    assert isinstance(result, Resource)


@pytest.fixture()
def sheets_auth():
    return Authentication(credential=credential_file, token=sheet_token_file, service="sheets")


def test_get_client_service_authorized_return_correct_values(sheets_auth):
    result = sheets_auth.get_service()
    assert isinstance(result, Resource)
