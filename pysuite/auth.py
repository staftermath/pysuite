from typing import Union, Optional
from pathlib import Path, PosixPath
import pickle
import logging

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

CREDENTIALS = {
    "drive":["token"],
    "sheet": ["token"]
}


class Authentication:
    SCOPE = None  # overload in child class

    def __init__(self, credential: Optional[Union[PosixPath, str, dict]], token: Optional[Union[PosixPath, str]]):
        self._token_path = Path(token)
        self._credential = self.load_credential(credential, token=token)

    def load_credential(self, credential: Optional[Union[PosixPath, str, dict]],
                        token: Optional[Union[PosixPath, str]]=None):
        if token is not None:
            return self._load_token(token)

        if credential is None:
            return self._load_credential_from_input()

        if isinstance(credential, str):
            credential = Path(credential)

        if isinstance(credential, PosixPath):
            return self._load_credential_from_file(credential)

        if isinstance(credential, dict):
            return self._load_credential_from_dict(credential)

    def _load_credential_from_file(self, file_path: PosixPath):
        return InstalledAppFlow.from_client_secrets_file(file_path, self.SCOPE)

    def _load_credential_from_dict(self, credential: dict):
        pass

    def _load_credential_from_input(self):
        pass

    def _load_token(self, token: Union[PosixPath, str, dict]):
        with open(token, 'rb') as f:
            credentials = pickle.load(f)

        if not isinstance(credentials, Credentials):
            raise TypeError(f"expecting Credentials type object from token file. got {type(credentials)} instead.")

        return credentials

    def refresh(self):
        if not self._credential.valid:
            if self._credential.expired and self._credential.refresh_token:
                self._credential.refresh(Request())
            else:
                # need to manually authenticate once
                self._credential.run_local_server(port=9999)

        self.write_token()

    def write_token(self):
        with open(self._token_path, 'wb') as token:
            pickle.dump(self._credential, token)

    def get_client(self):
        raise NotImplementedError