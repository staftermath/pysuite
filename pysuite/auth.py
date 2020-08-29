"""classes used to authenticate credentials and create service for Google Suite Apps
"""
from typing import Union, Optional
from pathlib import Path, PosixPath
import pickle
import json
import logging

from googleapiclient.discovery import build, Resource
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = {
    "drive": "https://www.googleapis.com/auth/drive",
    "sheets": "https://www.googleapis.com/auth/spreadsheets"
}

DEFAULT_VERSIONS = {
    "drive": "v3",
    "sheets": "v4"
}


class Authentication:
    """read from credential file and token file and authenticate with Google service for requested services. if token
    file does not exists, confirmation is needed from browser prompt and the token file will be created.
    """
    def __init__(self, credential: Optional[Union[PosixPath, str, dict]], token: Union[PosixPath, str], services: list):
        self._token_path = Path(token)
        self._credential_path = Path(credential)
        self._scopes = [SCOPES[service] for service in services]
        self._credential = self.load_credential(credential)
        self.refresh()

    def load_credential(self) -> Credentials:
        """load credential json file needed to authenticate Google Suite Apps. If token file does not exists,
        confirmation is needed from browser prompt and the token file will be created.

        :param credential: path to the credential json file.
        :return: a Credential object
        """
        if not Path(self._token_path).exists():
            return self._load_credential_from_file(self._credential_path)

        with open(self._credential_path, 'r') as f:
            cred_json = json.load(f)

        with open(self._token_path, 'r') as f:
            token_json = json.load(f)

        try:
            credential = Credentials(token=token_json.get("token"),
                                     refresh_token=token_json.get("refresh_token"),
                                     id_token=cred_json.get("id_token", None),
                                     token_uri=cred_json.get("token_uri"),
                                     client_id=cred_json.get("client_id"),
                                     client_secret=cred_json.get("client_secret"),
                                     scopes=self._scopes)
        except KeyError as e:
            logging.critical("missing key value in credential")
            raise e

        return credential

    def _load_credential_from_file(self, file_path: PosixPath) -> Credentials:
        """load credential json file and open web browser for confirmation.

        :param file_path: path to the credential json file.
        :return: a Credential object
        """
        flow = InstalledAppFlow.from_client_secrets_file(file_path, self._scopes)
        credential = flow.run_local_server(port=9999)
        return credential

    def refresh(self):
        """refresh token if not valid or has expired. In addition token file is overwritten.

        :return: None
        """
        if not self._credential.valid:
            if self._credential.expired and self._credential.refresh_token:
                self._credential.refresh(Request())

        self.write_token()

    def write_token(self):
        token_json = {
            "token": self._credential.token,
            "refresh_token": self._credential.refresh_token
        }
        with open(self._token_path, 'w') as token:
            json.dump(token_json, token)

    def get_service(self, service: str, version: Optional[str]=None):
        """get a service object for requested service. This service must be within authorized scope set up at
        initiation stage.

        :param service: service type. "drive" or "sheets"
        :param version: version of target service. if None, default version will be used. it varies with service.
        :return: a service object used to access API for that service.
        """
        if service not in DEFAULT_VERSIONS.keys():
            raise ValueError(f"service {version} not in {DEFAULT_VERSIONS.keys()}")

        if SCOPES[service] not in self._scopes:
            raise RuntimeError(f"Selected service has not been authorized. You need authenticate again with desires service")

        if version is None:
            version = DEFAULT_VERSIONS[service]

        return build(service, version, credentials=self._credential, cache_discovery=True)
