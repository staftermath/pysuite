"""implement api to access google drive
"""
import logging
from pathlib import PosixPath, Path
from typing import Union, Optional, List

from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload


class Drive:

    def __init__(self, service: Resource):
        self._service = service

    def download(self, id: str, to_file: Union[str, PosixPath]):
        """download the google drive file with the requested id to target local file.

        :param id: id of the google drive file
        :param to_file: local file path
        :return: None
        """
        request = self._service.files().get_media(fileId=id)
        with open(to_file, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logging.info(f"Download {status.progress()*100}%")

    def upload(self, from_file: Union[str, PosixPath], name: Optional[str]=None, mimetype: Optional[str]=None,
               parent_ids: Optional[List[str]]=None) -> str:
        """upload local file to gdrive.

        :param from_file: path to local file.
        :param name: name of google drive file. If None, the name of local file will be used.
        :param mimetype: Mime-type of the file. If None then a mime-type will be guessed from the file extension.
        :param parent_ids: list of ids for the folder you want to upload the file to. If None, it will be uploaded to
          root of Google drive.
        :return: id of the uploaded file
        """
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

        file = self._service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()
        return file.get("id")

    def update(self, id: str, from_file: Union[str, PosixPath]):
        """update the Google drive with local file.

        :param id: id of the Google drive file to be updated
        :param from_file: path to local file.
        :return: None
        """
        media = MediaFileUpload(str(from_file),
                                resumable=True)

        self._service.files().update(body=dict(), fileId=id, media_body=media).execute()

    def get_id(self, name: str, parent_id: Optional[str]=None):
        """get the id of the file with specified name. if more than one file are found, an error will be raised.

        :param name: name of the file to be searched.
        :param parent_id: id of the folder to limit the search. If None, the full Google drive will be searched.
        :return: the id of the file if found. Or None if no such name is found.
        """
        q = f"name = '{name}' and trashed = false"
        if parent_id is not None:
            q += f" and '{parent_id}' in parents"

        response = self._service.files().list(pageSize=10,
                                              fields=self._get_fields_query_string(),
                                              q=q).execute()

        item = response.get('files', None)
        if item is None:
            return None

        if len(item) > 1:
            raise RuntimeError(f"More than one file is found. Please rename the file with a unique string.")

        return item[0]['id']

    def list(self, id: str) -> list:
        """list the content of the folder by the given id.

        :param id: id of the folder to be listed.
        :return: a list of dictionaries containing id and name of the object contained in the target folder.
        """
        q = f"'{id}' in parents and trashed = false"
        result = []
        page_token = ""  # place holder to start the loop
        while page_token is not None:
            response = self._service.files().list(q=q,
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
        self._service.files().delete(fileId=id).execute()

    def create_folder(self, name: str, parent_ids: Optional[list]=None) -> str:
        """create a folder on google drive by the given name.

        :param name: name of the folder to be created.
        :param parent_ids: list of ids where you want to create your folder in.
        :return: id of the created folder.
        """
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

        folder = self._service.files().create(body=file_metadata, fields='id').execute()
        return folder.get("id")

    def share(self, id: str, emails: List[str], role: str= "reader", notify=True):  # pragma: no cover
        """modify the permission of the target object and share with the provided emails.

        :param id: id of target object.
        :param emails: list of emails to be shared with.
        :param role: type of permission. accepted values are: 'owner', 'organizer', 'fileOrganzier', 'writer',
          'commenter' and 'reader'.
        :param notify: Whether notifying emails about the sharing.
        :return: name of the object shared.
        """
        call_back = None
        batch = self._service.new_batch_http_request(callback=call_back)

        for email in emails:
            user_permission = {
                "type": "user",
                "role": role,
                "emailAddress": email
            }
            batch.add(self._service.permissions().create(
                fileId=id,
                body=user_permission,
                fields='id',
                sendNotification=notify
            ))
        batch.execute()
        return self.get_name(id)

    def _get_fields_query_string(self, fields: Optional[list]=None) -> str:
        """create a string used to query gdrive object and return requested fields.

        :param fields: list of fields to be returned in query.
        :return: a string used to query gdrive. only usable in `fields` arguments in list()
        """
        if fields is None:
            fields = ["id", "name"]

        if not isinstance(fields, list):
            raise TypeError(f"fields must be a list. got {type(fields)}")

        if len(fields) == 0:
            raise ValueError("fields cannot be empty")

        return f"nextPageToken, files({','.join(fields)})"

    def get_name(self, id: str) -> str:
        """get the name of the Google drive object.

        :param id: id of the target Google drive object
        :return: name of the object
        """
        file = self._service.files().get(fileId=id).execute()
        return file['name']
