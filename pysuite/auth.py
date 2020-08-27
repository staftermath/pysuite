"""classes used to authenticate credentials and create service for Google Suite Apps
"""
from typing import Union, Optional
from pathlib import Path, PosixPath
import pickle

from googleapiclient.discovery import build, Resource
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = {
    "drive": "https://www.googleapis.com/auth/drive",
    "spreadsheet": "https://www.googleapis.com/auth/spreadsheets"
}


class Authentication:
    SCOPE = None  # overload in child class
    def __init__(self, credential: Optional[Union[PosixPath, str, dict]], token: Union[PosixPath, str]):
        self._token_path = Path(token)
        self._credential = self.load_credential(credential)
        self.refresh()
        self.write_token()

    def load_credential(self, credential: Optional[Union[PosixPath, str]]) -> Credentials:
        """load credential json file needed to authenticate Google Suite Apps. If None is provided, token is loaded
        instead from self._token_path

        :param credential: path to the credential json file.
        :return: a Credential object
        """
        if self._token_path.exists():
            return self._load_token()

        if isinstance(credential, str):
            credential = Path(credential)

        return self._load_credential_from_file(credential)

    def _load_credential_from_file(self, file_path: PosixPath) -> Credentials:
        """load credential json file and open web browser for confirmation.

        :param file_path: path to the credential json file.
        :return: a Credential object
        """
        flow = InstalledAppFlow.from_client_secrets_file(file_path, self.SCOPE)
        credential = flow.run_local_server(port=9999)
        return credential

    def _load_token(self) -> Credentials:
        """load Credential object from token.

        :return: a Credential object
        """
        with open(self._token_path, 'rb') as f:
            credentials = pickle.load(f)

        if not isinstance(credentials, Credentials):
            raise TypeError(f"expecting Credentials type object from token file. got {type(credentials)} instead.")

        return credentials

    def refresh(self):
        """refresh token if not valid or has expired. This will overwrite the token file.

        :return: None
        """
        if not self._credential.valid:
            if self._credential.expired and self._credential.refresh_token:
                self._credential.refresh(Request())

        self.write_token()

    def write_token(self):
        with open(self._token_path, 'wb') as token:
            pickle.dump(self._credential, token)

    def get_service(self, version: str):
        raise NotImplementedError


class DriveAuth(Authentication):
    SCOPE = [SCOPES["drive"]]
    def get_service(self, version="v3") -> Resource:
        return build('drive', version, credentials=self._credential, cache_discovery=True)


class SheetAuth(Authentication):
    SCOPE = [SCOPES["spreadsheet"]]
    def get_service(self, version="v4") -> Resource:
        return build('sheets', version, credentials=self._credential, cache_discovery=True)
