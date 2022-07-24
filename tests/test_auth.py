import logging

import pytest
from pathlib import PosixPath
import json

from googleapiclient.discovery import Resource
from google.auth.exceptions import RefreshError
from google.cloud.vision_v1 import ImageAnnotatorClient
from google.cloud.storage.client import Client as StorageClient
from google.oauth2.credentials import Credentials

from pysuite.auth import Authentication, load_oauth, get_token_from_secrets_file


test_project_id = "pysuite-test"
credential_folder = PosixPath(__file__).resolve().parent.parent / "credentials"
client_secret_file = credential_folder / "secret_file.json"
token_file = credential_folder / "credential.json"


@pytest.mark.skip("this will prompt browser")
def test_load_from_file_correctly(tmpdir):
    token_path = PosixPath(tmpdir.join("test_load_from_file_token.json"))
    result = get_token_from_secrets_file(secret_file=client_secret_file, services=["drive", "sheets", "gmail", "vision", "storage"])
    with open(token_path, 'w') as fp:
        json.dump(result, fp)

    assert isinstance(result, dict)


@pytest.mark.parametrize(
    "credential",
    [
        token_file,
        json.load(open(token_file, 'r')),
        Credentials(**json.load(open(token_file, 'r'))),
    ]
)
def test_load_oauth_correctly(credential):
    result = load_oauth(credential)
    assert isinstance(result, Credentials)


def test_load_oauth_raise_error_with_bad_type():
    with pytest.raises(TypeError):
        load_oauth(123)


def test_authentication_log_correctly_when_refresh_error(caplog):
    cred_dict = {
        "client_id": "bad_client_id",
        "client_secret": "bad_client_secret",
        "refresh_token": "bad_refresh_token",
        "token": "bad_token",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    with pytest.raises(RefreshError), caplog.at_level(logging.CRITICAL):
        Authentication(credential=cred_dict)

    result = caplog.records[0].message
    expected = "Unable to refresh oauth credentials. You may need to manually update oauth file."
    assert expected == result


@pytest.fixture(scope="session")
def auth_fixture():
    return Authentication(credential=token_file, project_id=test_project_id)
