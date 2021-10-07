"""Implement api to access google storage API
"""
import logging
import json
from pathlib import PosixPath
from typing import Union, Optional, List

from google.cloud.storage.client import Client


class Storage:
    """Class to interact with Google Storage API.

    :param service: an authorized Google Storage service client.
    """

    def __init__(self, service: Client):
        self._service = service

    def upload(self, from_object: Union[str, PosixPath], to_object: str):
        pass

    def download(self, from_object: str, to_object: Union[str, PosixPath]):
        pass

    def remove(self, target_object: str):
        pass

    def move(self, from_object: str, to_object: str):
        pass

    def list(self, target_object: str):
        pass

    def create_bucket(self, bucket_name: str):
        pass

    def remove_bucket(self, bucket_name: str):
        pass

    def _split_gs_object(self, target_object: str) -> (str, str):
        GS_HEADER = "gs://"
        if not target_object.startswith(GS_HEADER):
            raise ValueError(f"{target_object} is not a valid gs object.")

        bucket, object_path = target_object[len(GS_HEADER):].split("/", 1)
        return bucket, object_path
