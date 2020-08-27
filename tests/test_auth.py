import pytest
from pathlib import Path
import pickle

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource

from pysuite.auth import DriveAuth, SheetAuth


credential_folder = Path(".").resolve().parent / "credentials"
credential_file = credential_folder / "credential.json"
token = credential_folder / "token.pickle"


@pytest.mark.skip("this will prompt browser")
def test_drive_auth_load_from_file_correctly(tmpdir):
    token_path = Path(tmpdir.join("test_load_from_file_token.pickle"))
    result = DriveAuth(credential=credential_file, token=token_path)
    assert result._credential.valid
    assert not result._credential.expired

    with open(token_path, 'rb') as token:
        credential = pickle.load(token)

    assert isinstance(credential, Credentials)


@pytest.fixture()
def drive_auth():
    return DriveAuth(credential=credential_file, token=token)


def test_drive_auth_load_from_token_correctly(drive_auth):
    assert drive_auth._credential.valid
    assert not drive_auth._credential.expired


def test_drive_auth_get_client_return_correct_values(drive_auth):
    result = drive_auth.get_service()
    assert isinstance(result, Resource)


@pytest.fixture()
def sheet_auth():
    return SheetAuth(credential=None, token=token)


def test_sheet_auth_get_client_return_correct_values(sheet_auth):
    result = sheet_auth.get_service()
    assert isinstance(result, Resource)
