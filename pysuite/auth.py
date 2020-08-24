from typing import Union, Optional
from pathlib import Path, PosixPath
import pickle
import logging

from google.oauth2.credentials import Credentials

CREDENTIALS = {
    "drive":["token"],
    "sheet": ["token"]
}


class Authentication:

    def __init__(self, credential: Optional[Union[PosixPath, str, dict]], token: Optional[Union[PosixPath, str]]=None):
        self._credential = self.load_credential(credential, token=token)
        self.refresh()

    def load_credential(self, credential: Optional[Union[PosixPath, str, dict]],
                        token: Optional[Union[PosixPath, str]]=None):
        if token is not None:
            return self._load_token(token)

        if credential is None:
            return self._load_credentail_from_input()

        if isinstance(credential, str):
            credential = Path(credential)

        if isinstance(credential, PosixPath):
            return self._load_credential_from_file(credential)

        if isinstance(credential, dict):
            return self._load_credential_from_dict(credential)

    def _load_credential_from_file(self, file_path: PosixPath):
        pass

    def _load_credential_from_dict(self, credential: dict):
        pass

    def _load_credentail_from_input(self):
        pass

    def _load_token(self, token: Union[PosixPath, str, dict]):
        with open(token, 'rb') as f:
            credentials = pickle.load(f)

        if not isinstance(credentials, Credentials):
            raise TypeError(f"expecting Credentials type object from token file. got {type(credentials)} instead.")

        return credentials

    def refresh(self):
        pass

    def get_client(self):
        raise NotImplementedError