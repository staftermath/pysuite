"""classes used to authenticate credentials and create service for Google Suite Apps
"""
import json
import logging
from pathlib import PosixPath
from typing import Union, Optional, List
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials


SCOPES = {
    "drive": "https://www.googleapis.com/auth/drive",
    "sheets": "https://www.googleapis.com/auth/spreadsheets",
    "gmail": "https://www.googleapis.com/auth/gmail.compose",
    "vision": "https://www.googleapis.com/auth/cloud-vision",
    "storage": "https://www.googleapis.com/auth/cloud-platform",
}

CLOUD_SERVICES = {"vision", "storage"}

DEFAULT_VERSIONS = {
    "drive": "v3",
    "sheets": "v4",
    "gmail": "v1",
    "vision": "v1",
    "storage": None,
}


def get_token_from_secrets_file(secret_file, scopes: Optional[List[str]] = None,
                                services: Optional[List[str]] = None, **kwargs) -> dict:  # pragma: no cover
    """Generates oauth credential dictionary from OAuth client secret file.

    :param secret_file: Path to the client secret file.
    :param scopes: A list of Google API scopes. If None, `services` must be provided.
    :param services: A list of supported services by pysuite.
    :param kwargs: Additional arguments for `Flow.from_client_secrets_file`.
    :return: A dictionary containing oauth credentials.
    """
    if scopes is None and services is None:
        raise ValueError("Scopes or services required.")
    if scopes is None:
        scopes = [SCOPES[service] for service in services]

    flow = Flow.from_client_secrets_file(secret_file, scopes=scopes, **kwargs)
    flow.redirect_uri = "https://console.developers.google.com/apis/credentials"
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true"
    )
    print("=== Copy the following URL in browser and accept authorization ===")
    print(authorization_url)
    authorization_response = input("Copy the URL from redirected page here.").strip()
    flow.fetch_token(authorization_response=authorization_response)
    credentials = flow.credentials.to_json()
    print("Save the following content as json file.")
    print(credentials)
    return credentials


def load_oauth(credential) -> Credentials:
    """Loads various types of object to create Credentials object needed to authenticate Google Suite Apps.

    :param credential: path to the credential json file, or pre-generated Credentials object, or a dictionary containing
      OAuth credentials.
    :return: a Credential object.
    """
    if isinstance(credential, Credentials):
        return credential

    if isinstance(credential, str) or isinstance(credential, PosixPath):
        with open(credential, 'r') as fp:
            return Credentials(**json.load(fp))

    if isinstance(credential, dict):
        return Credentials(**credential)

    raise TypeError(f"Expecting str, PosixPath, dict or Credentials. Got {type(credential)}.")


class Authentication:
    """Accepts various types of credentials and authenticate with Google service for requested services.

    You can pass a list of services or one service.
    """
    def __init__(self, credential: Union[PosixPath, str, Credentials, dict], project_id: Optional[str] = None):
        """Instantiates an Authentication object.

        :param credential: path to the credential json file, or pre-generated Credentials object, or a dictionary
          containing OAuth credentials.
        :param project_id: Project id for the provided credentials. You can get it from Google Cloud Console. This is
          needed if "storage" service is requested.
        """
        self.credential = load_oauth(credential)
        self.project_id = project_id
        self.refresh()

    def refresh(self):
        """Refreshes token if not valid or has expired.
        """
        request = Request()
        try:
            self.credential.refresh(request)
        except RefreshError:
            logging.critical('Unable to refresh oauth credentials. You may need to manually update oauth file.')
            raise
