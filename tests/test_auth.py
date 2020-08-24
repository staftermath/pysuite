import pytest
from pathlib import Path
import pickle

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource

from pysuite.auth import GoogleDriveClient, GoogleSheetClient


credential_folder = Path(".").resolve().parent / "credentials"
gdrive_credential = credential_folder / "gdrive.json"
gdrive_token = credential_folder / "token.pickle"


@pytest.mark.skip("this will prompt browser")
def test_gdrive_load_from_file_correctly(tmpdir):
    token_path = Path(tmpdir.join("test_load_from_file_token.pickle"))
    result = GoogleDriveClient(credential=gdrive_credential, token=token_path)
    assert result._credential.valid
    assert not result._credential.expired

    with open(token_path, 'rb') as token:
        credential = pickle.load(token)

    assert isinstance(credential, Credentials)


@pytest.fixture()
def drive_client():
    return GoogleDriveClient(credential=None, token=gdrive_token)


def test_gdrive_load_from_token_correctly(drive_client):
    assert drive_client._credential.valid
    assert not drive_client._credential.expired


def test_gdrive_get_client_return_correct_values(drive_client):
    result = drive_client.get_client()
    assert isinstance(result, Resource)


@pytest.fixture()
def sheet_client():
    return GoogleSheetClient(credential=None, token=gdrive_token)


def test_google_sheet_client_get_client_return_correct_values(sheet_client):
    result = sheet_client.get_client()
    assert isinstance(result, Resource)
