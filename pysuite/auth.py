"""classes used to authenticate credentials and create service for Google Suite Apps
"""
import json
import logging
from pathlib import PosixPath
from typing import Union, Optional, List
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.cloud import vision as gv
from google.cloud import storage


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
                                services: Optional[List[str]] = None, **kwargs) -> dict:
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
    :return: a Credential object
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
    def __init__(self, credential: Union[PosixPath, str, Credentials, dict], services: Union[list, str],
                 project_id: Optional[str] = None):
        """

        :param credential: path to the credential json file, or pre-generated Credentials object, or a dictionary
          containing OAuth credentials.
        :param services: A list of services allowed by the provided credentials.
        :param project_id: Project id for the provided credentials. You can get it from Google Cloud Console.
        """
        self._credential = load_oauth(credential)
        self._project_id = project_id
        self._services = self._get_services(services)
        self._scopes = self._get_scopes()
        self.refresh()

    def refresh(self):
        """Refreshes token if not valid or has expired. In addition token file is overwritten.
        """
        request = Request()
        try:
            self._credential.refresh(request)
        except RefreshError:
            logging.critical('Unable to refresh oauth credentials. You may need to manually update oauth file.')
            raise

    def get_service_client(self, service: Optional[str] = None, version: Optional[str] = None):
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

        if service not in CLOUD_SERVICES:
            return build(service, version, credentials=self._credential, cache_discovery=True)
        elif service == "vision":
            return gv.ImageAnnotatorClient(credentials=self._credential)
        elif service == "storage":
            return storage.Client(project=self._project_id, credentials=self._credential)
        else:
            # Won't reach here
            raise ValueError(f"Invalid service: {service}. This is an implementation error.")  # pragma: no cover

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

        if set(services).intersection(CLOUD_SERVICES):
            diff = set(services).difference(CLOUD_SERVICES)
            if diff:
                raise ValueError(f"Google cloud services {CLOUD_SERVICES} cannot be mixed with non cloud services. "
                                 f"Found {diff}")

        return services

    @property
    def is_google_cloud(self):
        return set(self._services).issubset(CLOUD_SERVICES)
