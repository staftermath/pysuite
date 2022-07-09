import pytest
from pathlib import PosixPath
import json

from googleapiclient.discovery import Resource
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
    ("credential"),
    [
        token_file,
        json.load(open(token_file, 'r'))
    ]
)
def test_load_oauth_correctly(credential):
    result = load_oauth(credential)
    assert isinstance(result, Credentials)


def test_when_mixing_cloud_and_non_cloud_service_raise_exception_correctly():
    with pytest.raises(ValueError):
        Authentication(credential=token_file, services=["drive", "vision"])


@pytest.fixture(scope="session")
def drive_auth():
    return Authentication(credential=token_file, services="drive")


def test_get_client_from_drive_auth_return_correct_values(drive_auth):
    result = drive_auth.get_service_client()
    assert isinstance(result, Resource)


@pytest.fixture(scope="session")
def sheets_auth():
    return Authentication(credential=token_file, services="sheets")


def test_get_client_from_sheets_auth_return_correct_values(sheets_auth):
    result = sheets_auth.get_service_client()
    assert isinstance(result, Resource)


@pytest.fixture(scope="session")
def gmail_auth():
    return Authentication(credential=token_file, services="gmail")


def test_get_client_from_gmail_auth_return_correct_values(gmail_auth):
    result = gmail_auth.get_service_client()
    assert isinstance(result, Resource)


@pytest.fixture(scope="session")
def vision_auth():
    return Authentication(credential=token_file, services="vision")


def test_get_client_from_vision_auth_return_correct_values(vision_auth):
    result = vision_auth.get_service_client()
    assert isinstance(result, ImageAnnotatorClient)


@pytest.fixture(scope="session")
def multi_auth():
    return Authentication(credential=token_file,
                          services=["drive", "sheets", "gmail"])


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


@pytest.fixture(scope="session")
def storage_auth():
    return Authentication(credential=token_file, services="storage", project_id=test_project_id)


def test_get_client_from_storage_auth_return_correct_values(storage_auth):
    result = storage_auth.get_service_client()
    assert isinstance(result, StorageClient)
