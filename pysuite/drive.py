import logging

from pathlib import PosixPath
from typing import Union, Optional, List

from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload


class Drive:

    def __init__(self, client: Resource):
        self._client = client

    def download(self, id: str, to_file: Union[str, PosixPath]):
        request = self._client.files().get_media(fileId=id)
        with open(to_file, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logging.info(f"Download {status.progress()*100}%")

    def upload(self, from_file: Union[str, PosixPath], name: Optional[str]=None, mimetype: Optional[str]=None,
               parent_ids: Optional[List[str]]=None) -> str:
        pass

    def update(self, id: str, from_file: Union[str, PosixPath]):
        pass

    def get_id(self, name: str, parent_id: Optional[str]=None):
        q = f"name = '{name}' and trashed = false"
        if parent_id is not None:
            q += f" and '{parent_id}' in parents"

        response = self._client.files().list(pageSize=10,
                                           fields=self._get_fields_query_string(["id", "name"]),
                                           q=q).execute()

        item = response.get('files', None)
        if item is None:
            return None

        if len(item) > 1:
            raise RuntimeError(f"More than one file is found. Please rename the file with a unique string.")

        return item[0]['id']

    def list(self, id: str):
        pass

    def delete(self, id: str, recursive: bool=False):
        pass

    def create_folder(self, name: str, parent_ids: Optional[list]=None):
        pass

    def modify_sharing(self, id: str, emails: List[str], role: str="reader", notify=True):
        pass

    def _get_fields_query_string(self, fields: Optional[list]) -> str:
        if fields is None:
            fields = ["id", "name"]

        if not isinstance(fields, list):
            raise TypeError(f"fields must be a list. got {type(fields)}")

        if len(fields) == 0:
            raise ValueError("fields cannot be empty")

        return f"nextPageToken, files({','.join(fields)})"
