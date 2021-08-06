import pytest
from pathlib import Path
import json

from googleapiclient.discovery import Resource

from pysuite.auth import Authentication


credential_folder = Path(__file__).resolve().parent.parent / "credentials"
credential_file = credential_folder / "credential.json"
drive_token_file = credential_folder / "drive_token.json"
sheet_token_file = credential_folder / "sheets_token.json"
gmail_token_file = credential_folder / "gmail_token.json"
vision_token_file = credential_folder / "vision_token.json"
multi_token_file = credential_folder / "token.json"


@pytest.mark.skip("this will prompt browser")
def test_load_from_file_correctly(tmpdir):
    token_path = Path(tmpdir.join("test_load_from_file_token.json"))
    result = Authentication(credential=credential_file, token=token_path, services="drive")
    assert result._credential.valid
    assert not result._credential.expired


def test_invalid_service_raise_exception(tmpdir):
    with pytest.raises(ValueError):
        Authentication(credential=credential_file, token=Path(tmpdir.join("not_exist.json")), services="bad_service")


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
        Authentication(credential=credential_file, token=temp_token_file, services="drive")


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
        Authentication(credential=temp_credential_file, token=drive_token_file, services="drive")


@pytest.fixture(scope="session")
def drive_auth():
    return Authentication(credential=credential_file, token=drive_token_file, services="drive")


def test_get_client_from_drive_auth_return_correct_values(drive_auth):
    result = drive_auth.get_service_client()
    assert isinstance(result, Resource)


@pytest.fixture(scope="session")
def sheets_auth():
    return Authentication(credential=credential_file, token=sheet_token_file, services="sheets")


def test_get_client_from_sheets_auth_return_correct_values(sheets_auth):
    result = sheets_auth.get_service_client()
    assert isinstance(result, Resource)


@pytest.fixture(scope="session")
def gmail_auth():
    return Authentication(credential=credential_file, token=gmail_token_file, services="gmail")


def test_get_client_from_gmail_auth_return_correct_values(gmail_auth):
    result = gmail_auth.get_service_client()
    assert isinstance(result, Resource)


@pytest.fixture(scope="session")
def vision_auth():
    return Authentication(credential=credential_file, token=gmail_token_file, services="vision")


def test_get_client_from_vision_auth_return_correct_values(vision_auth):
    result = vision_auth.get_service_client()
    assert isinstance(result, Resource)


@pytest.fixture(scope="session")
def multi_auth():
    return Authentication(credential=credential_file,
                          token=multi_token_file,
                          services=["drive", "sheets", "gmail", "vision"])


@pytest.mark.parametrize("service",
                         ["drive", "sheets", "gmail"])
def test_get_service_when_multiple_service_authorized_return_service_correctly(multi_auth, service):
    result = multi_auth.get_service_client(service=service)
    assert isinstance(result, Resource)


def test_get_service_when_multiple_service_authorized_and_no_service_arg_passed_raise_exception(multi_auth):
    with pytest.raises(ValueError):
        multi_auth.get_service_client()


@pytest.mark.parametrize("service",
                         [None, "invalid_service"])
def test_get_service_when_service_not_authorized_raise_exception(multi_auth, service):
    with pytest.raises(ValueError):
        multi_auth.get_service_client(service=service)
