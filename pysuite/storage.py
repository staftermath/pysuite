"""Implement api to access google storage API
"""
import logging
import json
from pathlib import PosixPath, Path
from typing import Union, Optional, List

from google.cloud.storage.client import Client, Bucket


class Storage:
    """Class to interact with Google Storage API.

    :param service: an authorized Google Storage service client.
    """

    def __init__(self, service: Client):
        self._service = service

    def upload(self, from_object: Union[str, PosixPath], to_object: str):
        from_object: PosixPath = Path(from_object).resolve()
        if not from_object.exists():
            raise IOError(f"{from_object} does not exist.")

        _bucket, _gs_object = self._split_gs_object(to_object)
        bucket = self.get_bucket(bucket_name=_bucket)
        if from_object.is_file():
            blob = bucket.blob(_gs_object)
            blob.upload_from_filename(str(from_object))
        else:
            for _from, _to in _add_folder_tree_to_new_base_dir(from_object, _gs_object):
                if _from.is_file():
                    blob = bucket.blob(_to)
                    blob.upload_from_filename(str(_from))

    def download(self, from_object: str, to_object: Union[str, PosixPath]):
        to_object: PosixPath = Path(to_object)
        blobs = list(self.list(target_object=from_object))
        if len(blobs) == 1:
            # No way we can tell if it's a folder or file, always consider it as file
            blobs[0].download_to_filename(str(to_object / blobs[0].name))
        else:
            for blob in blobs:
                _to_file = to_object / blob.name
                _to_file.parent.mkdir(parents=True, exist_ok=True)
                blob.download_to_filename(str(_to_file))

    def remove(self, target_object: str):
        pass

    def move(self, from_object: str, to_object: str):
        pass

    def list(self, target_object: str):
        _bucket, _gs_object = self._split_gs_object(target_object=target_object)
        bucket = self.get_bucket(bucket_name=_bucket)
        blob_iterator = bucket.list_blobs(prefix=_gs_object)
        return blob_iterator

    def create_bucket(self, bucket_name: str) -> Bucket:
        return self._service.create_bucket(bucket_name)

    def get_bucket(self, bucket_name: str) -> Bucket:
        return self._service.get_bucket(bucket_name)

    def remove_bucket(self, bucket_name: str, force: bool = False):
        bucket = self._service.get_bucket(bucket_name)
        bucket.delete(force=force)

    def _split_gs_object(self, target_object: str) -> (str, str):
        GS_HEADER = "gs://"
        if not target_object.startswith(GS_HEADER):
            raise ValueError(f"{target_object} is not a valid gs object.")

        bucket, object_path = target_object[len(GS_HEADER):].split("/", 1)
        return bucket, object_path


def _add_folder_tree_to_new_base_dir(from_path: PosixPath, to_path: str):
    folder_tree = from_path.rglob("*")
    for f in folder_tree:
        relative_path = f.relative_to(from_path)
        yield f, to_path + "/" + str(relative_path)

