from typing import Union, Optional
from pathlib import Path, PosixPath


class Authentication:

    def __init__(self, credential: Optional[Union[PosixPath, str, dict]]):
        self._credentail = self.load_credential(credential)

    def load_credential(self, credential: Optional[Union[PosixPath, str, dict]]):
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

    def get_ga_client(self):
        pass