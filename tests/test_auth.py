import pytest
from pathlib import Path
import pickle

from google.oauth2.credentials import Credentials

from pysuite.auth import GoogleDrive

credential_folder = Path(".").resolve().parent / "credentials"
gdrive_credential = credential_folder / "gdrive.json"
gdrive_token = credential_folder / "gdrive_token.pickle"


@pytest.mark.skip("this will prompt browser")
def test_gdrive_load_from_file_correctly(tmpdir):
    token_path = Path(tmpdir.join("test_load_from_file_token.pickle"))
    result = GoogleDrive(credential=gdrive_credential, token=token_path)
    assert result._credential.valid
    assert not result._credential.expired

    with open(token_path, 'rb') as token:
        credential = pickle.load(token)

    assert isinstance(credential, Credentials)


def test_gdrive_load_from_token_correctly(tmpdir):
    result = GoogleDrive(credential=None, token=gdrive_token)
    assert result._credential.valid
    assert not result._credential.expired
