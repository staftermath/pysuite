import pytest
from pathlib import Path
import pickle

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource

from pysuite.auth import Authentication


credential_folder = Path(".").resolve().parent / "credentials"
credential_file = credential_folder / "credential.json"
drive_token_file = credential_folder / "drive_token.json"  # "token.pickle"
sheet_token_file = credential_folder / "sheet_token.json"


@pytest.mark.skip("this will prompt browser")
def test_load_from_file_correctly(tmpdir):
    token_path = Path(tmpdir.join("test_load_from_file_token.json"))
    result = Authentication(credential=credential_file, token=token_path, service="drive")
    assert result._credential.valid
    assert not result._credential.expired


@pytest.fixture()
def drive_auth():
    return Authentication(credential=credential_file, token=drive_token_file, service="drive")


def test_get_client_no_service_provided_return_correct_values(drive_auth):
    result = drive_auth.get_service()
    assert isinstance(result, Resource)


@pytest.fixture()
def sheet_auth():
    return Authentication(credential=credential_file, token=sheet_token_file, service="sheets")


def test_get_client_service_authorized_return_correct_values(sheet_auth):
    result = sheet_auth.get_service("sheets")
    assert isinstance(result, Resource)


def test_get_client_service_unauthorized_raise_exception_correctly():
    with pytest.raises(ValueError):
        Authentication(credential=credential_file, token=sheet_token_file, service="drive")
