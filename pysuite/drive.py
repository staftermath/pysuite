import logging

from pathlib import PosixPath, Path
from typing import Union, Optional, List

from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload


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
        file_metadata = {'name': name if name is not None else Path(from_file).name}

        if parent_ids is not None:
            if not isinstance(parent_ids, list):
                raise TypeError(f"parent_ids must be a list. got {type(parent_ids)}")

            if len(parent_ids) == 0:
                raise ValueError(f"parent_ids cannot be empty")

            file_metadata["parents"] = parent_ids

        media = MediaFileUpload(str(from_file),
                                mimetype=mimetype,
                                resumable=True)

        file = self._client.files().create(body=file_metadata,
                                           media_body=media,
                                           fields='id').execute()
        return file.get("id")

    def update(self, id: str, from_file: Union[str, PosixPath]):
        media = MediaFileUpload(str(from_file),
                                resumable=True)

        self._client.files().update(body=dict(), fileId=id, media_body=media).execute()
        return id

    def get_id(self, name: str, parent_id: Optional[str]=None):
        q = f"name = '{name}' and trashed = false"
        if parent_id is not None:
            q += f" and '{parent_id}' in parents"

        response = self._client.files().list(pageSize=10,
                                             fields=self._get_fields_query_string(),
                                             q=q).execute()

        item = response.get('files', None)
        if item is None:
            return None

        if len(item) > 1:
            raise RuntimeError(f"More than one file is found. Please rename the file with a unique string.")

        return item[0]['id']

    def list(self, id: str):
        q = f"'{id}' in parents and trashed = false"
        result = []
        page_token = ""  # place holder to start the loop
        while page_token is not None:
            response = self._client.files().list(q=q,
                                                 spaces='drive',
                                                 fields=self._get_fields_query_string(),
                                                 pageToken=page_token).execute()
            result.extend(response.get("files", []))
            page_token = response.get("nextPageToken", None)

        return result

    def delete(self, id: str, recursive: bool=False):
        """delete target file from google drive
        TODO: implement recursive delete

        :param id: id of target object.
        :param recursive: if True and target id represents a folder, remove all nested files and folders.
        :return: None
        """
        self._client.files().delete(fileId=id).execute()

    def create_folder(self, name: str, parent_ids: Optional[list]=None):
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_ids is not None:
            if not isinstance(parent_ids, list):
                raise TypeError(f"parent_ids must be a list. got {type(parent_ids)}")

            if len(parent_ids) == 0:
                raise ValueError(f"parent_ids cannot be empty")

            file_metadata["parents"] = parent_ids

        folder = self._client.files().create(body=file_metadata, fields='id').execute()
        return folder.get("id")

    def modify_sharing(self, id: str, emails: List[str], role: str="reader", notify=True):  # pragma: no cover
        call_back = None
        batch = self._client.new_batch_http_request(callback=call_back)

        for email in emails:
            user_permission = {
                "type": "user",
                "role": role,
                "emailAddress": email
            }
            batch.add(self._client.permissions().create(
                fileId=id,
                body=user_permission,
                fields='id',
                sendNotification=notify
            ))
        batch.execute()
        return self.get_name(id)

    def _get_fields_query_string(self, fields: Optional[list]=None) -> str:
        if fields is None:
            fields = ["id", "name"]

        if not isinstance(fields, list):
            raise TypeError(f"fields must be a list. got {type(fields)}")

        if len(fields) == 0:
            raise ValueError("fields cannot be empty")

        return f"nextPageToken, files({','.join(fields)})"

    def get_name(self, id: str) -> str:
        file = self._client.files().get(fileId=id).execute()
        return file['name']
