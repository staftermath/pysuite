"""Implement api to access google storage API
"""
from pathlib import PosixPath, Path
from typing import Union

from google.cloud.storage.client import Client, Bucket

GS_HEADER = "gs://"


class Storage:
    """Class to interact with Google Storage API.

    :param service: an authorized Google Storage service client.
    """

    def __init__(self, service: Client):
        self._service = service

    def upload(self, from_object: Union[str, PosixPath], to_object: str):
        """Upload a file or a folder to google storage. If `from_object` is a folder, this method will
        upload it recursively.

        :param from_object: Path to the local file or folder to be uploaded.
        :param to_object: Target Google storage object location. If `from_object` is a file, this will be a file. If
          `from_object` is a folder, this will be a folder. This is a string that looks like "gs://xxxxx"
        :return: None
        """
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
        """Download target Google storage file or folder to local. If `from_object` is a folder, this method will
        download it recursively.

        :param from_object: Target Google storage path to be downloaded. This is a string that looks like "gs://xxxx"
        :param to_object: Path to the local file or folder. If `from_object` is a file, this will be a file. If
          `from_object` is a folder, this will be a folder.
        :return: None
        """
        to_object: PosixPath = Path(to_object)
        blobs = list(self.list(target_object=from_object))
        if len(blobs) == 1:
            # No way we can tell if it's a folder or file, always consider it as file
            blobs[0].download_to_filename(str(to_object))
        else:
            for blob in blobs:
                _to_file = to_object / blob.name
                _to_file.parent.mkdir(parents=True, exist_ok=True)
                blob.download_to_filename(str(_to_file))

    def remove(self, target_object: str):
        """Remove target Google storage file or folder. If `target_object` is a folder, this will remove it recursively.

        :param target_object: Target Google storage file or folder. This is a string that looks like "gs://xxxx"
        :return: None
        """
        _bucket, _ = self._split_gs_object(target_object)
        bucket = self.get_bucket(bucket_name=_bucket)
        bucket.delete_blobs(blobs=list(self.list(target_object=target_object)))

    def copy(self, from_object: str, to_object: str):
        """Copy Google storage file or folder from one location to another. If `from_object` is a folder, this will
        copy it recursively.

        :param from_object: Source Google storage file or folder. This is a string that looks like "gs://xxxx"
        :param to_object: Destination Google storage file or folder. This is a string that looks like "gs://xxxx"
        :return: None
        """
        _src_bucket, _src_gs_object = self._split_gs_object(from_object)
        _dest_bucket, _dest_prefix = self._split_gs_object(to_object)
        src_bucket = self.get_bucket(_src_bucket)
        dest_bucket = self.get_bucket(_dest_bucket)
        blobs = list(src_bucket.list_blobs(prefix=_src_gs_object))
        if len(blobs) == 1:
            src_bucket.copy_blob(blobs[0], dest_bucket, _dest_prefix)
        else:
            _src_prefix_len = len(_src_gs_object)
            for blob in blobs:
                name = blob.name
                _dest_gs_object = _dest_prefix + name[_src_prefix_len:]
                src_bucket.copy_blob(blob, dest_bucket, _dest_gs_object)

    def list(self, target_object: str):
        """Search Google storage target location and return an iterator. This iterator generates all files under the
        target location. If the target is a single file, the iterator only one object.

        :param target_object: Target Google storage location. This could be a file or a folder. This is a string that
          looks like "gs://xxxxx"
        :return: An iterator that iterates over the target location. Each item is a Blob object.
        """
        _bucket, _gs_object = self._split_gs_object(target_object=target_object)
        bucket = self.get_bucket(bucket_name=_bucket)
        blob_iterator = bucket.list_blobs(prefix=_gs_object)
        return blob_iterator

    def create_bucket(self, bucket_name: str) -> Bucket:
        """Create a bucket in Google Storage.

        :param bucket_name: The name of the Google storage bucket.
        :return: None
        """
        return self._service.create_bucket(bucket_name)

    def get_bucket(self, bucket_name: str) -> Bucket:
        """Get a Bucket object for the target Google storage bucket.

        :param bucket_name: The name of the target bucket.
        :return: A Bucket object for the target bucket.
        """
        return self._service.get_bucket(bucket_name)

    def remove_bucket(self, bucket_name: str, force: bool = False):
        """Remove the target bucket.

        :param bucket_name: Target bucket name.
        :param force: Whether force remove the target bucket. If True, even if the bucket is not empty, it will be
          removed. Default is False.
        :return:
        """
        bucket = self._service.get_bucket(bucket_name)
        bucket.delete(force=force)

    def _split_gs_object(self, target_object: str) -> (str, str):
        """Split a string that looks like "gs://bucket_name/object/path" into bucket name and object path. If it is not
        a valid gs path, an ValueError will be raised.

        :param target_object: Target google storage path.
        :return: A tuple of string. (bucket name, object path)
        """
        if not is_gcs_uri(target_uri=target_object):
            raise ValueError(f"{target_object} is not a valid gs object.")

        bucket, object_path = target_object[len(GS_HEADER):].split("/", 1)
        return bucket, object_path


def is_gcs_uri(target_uri: str):
    return isinstance(target_uri, str) and target_uri.startswith(GS_HEADER)


def _add_folder_tree_to_new_base_dir(from_path: PosixPath, to_path: str) -> (PosixPath, str):
    """Construct Google storage folder tree based on local folder tree so that the hierarchy is maintained.

    :param from_path: Path to a local folder.
    :param to_path: Path to the target Google storage folder.
    :return: Iterate and yield tuples of (local file, corresponding Google storage file Path)
    """
    folder_tree = from_path.rglob("*")
    for f in folder_tree:
        relative_path = f.relative_to(from_path)
        yield f, to_path + "/" + str(relative_path)
