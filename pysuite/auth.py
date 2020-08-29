"""classes used to authenticate credentials and create service for Google Suite Apps
"""
from typing import Union, Optional
from pathlib import Path, PosixPath
import json
import logging

from googleapiclient.discovery import build
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
    file does not exists, confirmation is needed from browser prompt and the token file will be created. You can pass
    a list of services or one service.
    """
    def __init__(self, token: Union[PosixPath, str], credential: Optional[Union[PosixPath, str]]=None, service: Optional[str]=None):
        self._token_path = Path(token)
        self._credential_path = Path(credential) if credential is not None else None
        self._service = service
        self._credential = self.load_credential()
        self.refresh()

    def load_credential(self) -> Credentials:
        """load credential json file needed to authenticate Google Suite Apps. If token file does not exists,
        confirmation is needed from browser prompt and the token file will be created.

        :param credential: path to the credential json file.
        :return: a Credential object
        """
        if not Path(self._token_path).exists():
            if self._service is None:
                raise ValueError("service must not be None when token file does not exists")

            return self._load_credential_from_file(self._credential_path)

        with open(self._token_path, 'r') as f:
            token_json = json.load(f)
            try:
                assert token_json["service"] == self._service
            except AssertionError:
                raise ValueError(f"token file does not contain token for the requested service. "
                                 f"Requested {self._service}. Got {token_json['service']}")

        scopes = self._get_scopes(self._service)
        try:
            credential = Credentials(token=token_json["token"],
                                     refresh_token=token_json["refresh_token"],
                                     scopes=scopes)
        except KeyError as e:
            logging.critical("missing key value in credential")
            raise e

        return credential

    def _load_credential_from_file(self, file_path: PosixPath) -> Credentials:
        """load credential json file and open web browser for confirmation.

        :param file_path: path to the credential json file.
        :return: a Credential object
        """
        scopes = self._get_scopes(self._service)
        flow = InstalledAppFlow.from_client_secrets_file(file_path, scopes)
        credential = flow.run_local_server(port=9999)
        return credential

    def refresh(self):
        """refresh token if not valid or has expired. In addition token file is overwritten.
        TODO: check scope of token/refresh_token to prevent accidental use of tokens with mismatching scope.

        :return: None
        """
        if not self._credential.valid:
            if self._credential.expired and self._credential.refresh_token:
                self._credential.refresh(Request())

        self.write_token()

    def write_token(self):
        token_json = {
            "token": self._credential.token,
            "refresh_token": self._credential.refresh_token,
            "service": self._service
        }
        with open(self._token_path, 'w') as token:
            json.dump(token_json, token)

    def get_service(self, service: Optional[str]=None, version: Optional[str]=None):
        """get a service object for requested service. This service must be within authorized scope set up at
        initiation stage.

        :param service: service type. "drive" or "sheets"
        :param version: version of target service. if None, default version will be used. it varies with service.
        :return: a service object used to access API for that service.
        """
        if service is not None and not isinstance(service, str):
            raise TypeError("service must be a str or None")

        if service is None:
            if isinstance(self._service, str):
                service = self._service
            else:
                raise ValueError("more than 1 service was authorized. service cannot be None")
        else:
            if service not in DEFAULT_VERSIONS.keys():
                raise ValueError(f"service {version} not in {DEFAULT_VERSIONS.keys()}")

            if (isinstance(self._service, list) and service not in self._service) or \
               (isinstance(self._service, str) and service != self._service):
                raise RuntimeError(f"Selected service has not been authorized. "
                                   f"You need authenticate again with desires service")

        if version is None:
            version = DEFAULT_VERSIONS[service]

        return build(service, version, credentials=self._credential, cache_discovery=True)

    def _get_scopes(self, service: str):
        try:
            scope = SCOPES[service]
            return scope
        except KeyError as e:
            logging.critical(f"{service} is not a valid service. expecting {SCOPES.keys()}")
            raise e
