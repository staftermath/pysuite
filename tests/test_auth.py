import pytest
from pathlib import Path
import pickle

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource

from pysuite.auth import Authentication


credential_folder = Path(".").resolve().parent / "credentials"
credential_file = credential_folder / "credential.json"
token_file = credential_folder / "token.json"  # "token.pickle"


@pytest.mark.skip("this will prompt browser")
def test_drive_auth_load_from_file_correctly(tmpdir):
    token_path = Path(tmpdir.join("test_load_from_file_token.json"))
    result = Authentication(credential=credential_file, token=token_path, services=["drive", "sheet"])
    assert result._credential.valid
    assert not result._credential.expired


@pytest.fixture()
def drive_auth():
    return Authentication(credential=credential_file, token=token_file, services=["drive"])


def test_drive_auth_load_from_token_correctly(drive_auth):
    assert drive_auth._credential.valid
    assert not drive_auth._credential.expired


def test_drive_auth_get_client_return_correct_values(drive_auth):
    result = drive_auth.get_service("drive")
    assert isinstance(result, Resource)


@pytest.fixture()
def sheet_auth():
    return Authentication(credential=credential_file, token=token_file, services=["sheets"])


def test_sheet_auth_get_client_return_correct_values(sheet_auth):
    result = sheet_auth.get_service("sheets")
    assert isinstance(result, Resource)
