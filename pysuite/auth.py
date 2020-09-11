"""classes used to authenticate credentials and create service for Google Suite Apps
"""
from typing import Union, Optional
from pathlib import Path, PosixPath
import json
import logging
import warnings
import functools
import re
import time
import random

from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

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
    def __init__(self, credential: Union[PosixPath, str], token: Union[PosixPath, str], services: Union[list, str]):
        self._token_path = Path(token)
        self._credential_path = Path(credential)
        self._services = self._get_services(services)
        self._scopes = self._get_scopes()
        self._credential = self.load_credential()
        self.refresh()

    def load_credential(self) -> Credentials:
        """load credential json file needed to authenticate Google Suite Apps. If token file does not exists,
        confirmation is needed from browser prompt and the token file will be created.

        :param credential: path to the credential json file.
        :return: a Credential object
        """
        if not Path(self._token_path).exists():
            return self._load_credential_from_file(self._credential_path)

        with open(self._token_path, 'r') as f:
            token_json = json.load(f)

        with open(self._credential_path, 'r') as f:
            try:
                cred_json = json.load(f)["installed"]
            except KeyError:
                raise KeyError("'installed' does not exist in credential file. please check the format")

        try:
            credential = Credentials(token=token_json["token"],
                                     refresh_token=token_json["refresh_token"],
                                     token_uri=cred_json["token_uri"],
                                     client_id=cred_json["client_id"],
                                     client_secret=cred_json["client_secret"],
                                     scopes=self._scopes,
                                     )
        except KeyError as e:
            logging.critical("missing key value in credential or token file")
            raise e

        return credential

    def _load_credential_from_file(self, file_path: PosixPath) -> Credentials:
        """load credential json file and open web browser for confirmation.

        :param file_path: path to the credential json file.
        :return: a Credential object
        """
        if self._services is None:
            raise ValueError("service must not be None when token file does not exists")

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

    def get_service_client(self, service: Optional[str]=None, version: Optional[str]=None):
        """get a service object for requested service. This service must be within authorized scope set up at
        initiation stage.

        :param service: type of service, "drive" or "sheets". If None and self._services has more than 1 items, an
          exception will be raised.
        :param version: version of target service. if None, default version will be used. it varies with service.
        :return: a service object used to access API for that service.
        """
        if service is None:
            if len(self._services) > 1:
                raise ValueError(f"service cannot be inferred. the authorized services are {self._services}")

            service = self._services[0]
        elif service not in self._services:
            raise ValueError(f"service {service} is not among authorized services: {self._services}")

        if version is None:
            version = DEFAULT_VERSIONS[service]

        return build(service, version, credentials=self._credential, cache_discovery=True)

    def _get_scopes(self) -> list:
        try:
            scopes = [SCOPES[service] for service in self._services]
            return scopes
        except KeyError as e:
            logging.critical(f"{self._services} is not a valid service. expecting {SCOPES.keys()}")
            raise e

    def _get_services(self, services: Union[list, str]) -> list:
        if isinstance(services, str):
            services = [services]
        if not set(services).issubset(SCOPES.keys()):
            raise ValueError(f"invalid services. got {services}, expecting {SCOPES.keys()}")

        return services


class ErrorHandler:
    """class used to retry on specific type error with specific error message pattern.
    """
    def __init__(self, exception: Exception, pattern: Optional[str]=None, max_retry: int=3, sleep: Union[int, float]=5):
        self._exception = exception
        self._max_retry = max_retry
        self._pattern = re.compile(pattern)
        self._sleep = sleep

    def __call__(self, func):
        exception = self._exception
        pattern = self._pattern
        @functools.wraps(func)
        def wrapper_func(*args, **kwargs):
            remaining_retries = self._max_retry
            while True:
                try:
                    result = func(*args, **kwargs)
                    return result
                except exception as e:
                    if pattern.match(str(e)) and remaining_retries > 0:
                        remaining_retries -= 1
                        warnings.warn(f"handled exception {e}. remaining retry: {remaining_retries}", UserWarning)
                        sleep = (self._max_retry - remaining_retries)*self._sleep + random.uniform(0, self._sleep)
                        time.sleep(sleep)
                        continue
                    raise e

        return wrapper_func


def handle_rate_exceeded_exception(sleep: Union[int, float]=5):
    """a class wrapper to give all non-hidden methods in a class ability to handle HttpError when user rate limit
    or quota exceeded

    :param sleep: number of seconds to sleep after each capture
    :return: a class decorator
    """
    decorator = ErrorHandler(exception=HttpError, pattern=".*[User Rate Limit Exceeded|Quota exceeded].*", sleep=sleep)
    def decorate(cls):
        for attr in cls.__dict__:  # there's propably a better way to do this
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate
