"""implement api to access google drive
"""
import logging
from pathlib import PosixPath, Path
from typing import Union, Optional, List
import re

from googleapiclient.discovery import build
from googleapiclient.discovery import Resource
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

from pysuite.auth import Authentication
from pysuite.utilities import retry_on_out_of_quota, MAX_RETRY_ATTRIBUTE, SLEEP_ATTRIBUTE


def _get_client(auth: Authentication, version: str) -> Resource:
    return build("drive", version, credentials=auth.credential)


class Drive:
    """Class to interact with Google Drive API

    :param auth: an authorized Google Drive service client.
    :param max_retry: max number of retry on quota exceeded error. if 0 or less, no retry will be attempted.
    :param sleep: base number of seconds between retries. the sleep time is exponentially increased after each retry.
    """

    def __init__(self, auth: Authentication, version: str = "v3", max_retry: int = 0, sleep: int = 5):
        self._client = _get_client(auth, version)
        setattr(self, MAX_RETRY_ATTRIBUTE, max_retry)
        setattr(self, SLEEP_ATTRIBUTE, sleep)

    @retry_on_out_of_quota()
    def download(self, id: str, to_file: Union[str, PosixPath]):
        """download the google drive file with the requested id to target local file.

        :param id: id of the google drive file
        :param to_file: local file path
        :return: None
        """
        request = self._client.files().get_media(fileId=id)
        with open(to_file, 'wb') as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logging.info(f"Download {status.progress()*100}%")

    @retry_on_out_of_quota()
    def upload(self, from_file: Union[str, PosixPath], name: Optional[str]=None, mimetype: Optional[str]=None,
               parent_id: Optional[str] = None) -> str:
        """upload local file to gdrive.

        :param from_file: path to local file.
        :param name: name of google drive file. If None, the name of local file will be used.
        :param mimetype: Mime-type of the file. If None then a mime-type will be guessed from the file extension.
        :param parent_id: id of the folder you want to upload the file to. If None, it will be uploaded to
          root of Google drive.
        :return: id of the uploaded file
        """
        file_metadata = {'name': name if name is not None else Path(from_file).name}

        if parent_id is not None:
            file_metadata["parents"] = parent_id

        media = MediaFileUpload(str(from_file),
                                mimetype=mimetype,
                                resumable=True)

        file = self._client.files().create(body=file_metadata,
                                           media_body=media,
                                           fields='id').execute()
        return file.get("id")

    @retry_on_out_of_quota()
    def update(self, id: str, from_file: Union[str, PosixPath]):
        """update the Google drive with local file.

        :param id: id of the Google drive file to be updated
        :param from_file: path to local file.
        :return: None
        """
        media = MediaFileUpload(str(from_file),
                                resumable=True)

        self._client.files().update(body=dict(), fileId=id, media_body=media).execute()

    @retry_on_out_of_quota()
    def get_id(self, name: str, parent_id: Optional[str]=None):
        """get the id of the file with specified name. if more than one file are found, an error will be raised.

        :param name: name of the file to be searched.
        :param parent_id: id of the folder to limit the search. If None, the full Google drive will be searched.
        :return: the id of the file if found. Or None if no such name is found.
        """
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

    @retry_on_out_of_quota()
    def find(self, name_contains: Optional[str]=None, name_not_contains: Optional[str]=None,
             parent_id: Optional[str]=None) -> list:
        """find all files whose name contain specified string and do not contain specified string. Note that Google
        API has unexpected behavior when searching for strings in name. It is can only search first 26 character. In
        addition, it seems to search from first alphabetic character and Assume there are the following files:
        'positive_a', 'positive_b', 'a', '_a', 'ba'

        :example:

        >>> self.find(name_contains='a')  # this finds only 'a' and '_a', not 'positive_a' or 'ba'

        :param name_contains: a string contained in the name
        :param name_not_contains: a string that is not contained in the name
        :param parent_id: parent folder id
        :return: a list of dictionaries containing id and name of found files.
        """
        if name_contains is None and name_not_contains is None:
            raise ValueError("name_contains and name_not_contains cannot both be None")

        q_name_contains = ""
        q_name_not_contains = ""
        if name_contains is not None:
            q_name_contains = f"and name contains '{name_contains}'"
        if name_not_contains is not None:
            q_name_not_contains = f"and not name contains '{name_not_contains}'"
        q = f"trashed = false {q_name_contains} {q_name_not_contains}"

        if parent_id is not None:
            q += f" and '{parent_id}' in parents"
        response = self._client.files().list(pageSize=100,
                                             fields=self._get_fields_query_string(),
                                             q=q).execute()
        item = response.get('files', [])
        return item

    @retry_on_out_of_quota()
    def list(self, id: str, regex: str=None, recursive: bool=False, depth: int=3) -> list:
        """list the content of the folder by the given id.

        :param id: id of the folder to be listed.
        :param regex: an regular expression used to filter returned file and folders.
        :param recursive: if True, children of the folder will also be listed.
        :param depth: number of recursion if recursive is True. This is to prevent cyclic nesting or deep nested folders.
        :return: a list of dictionaries containing id, name of the object contained in the target folder and list of
          parent ids.
        """
        q = f"'{id}' in parents and trashed = false"
        result = []
        page_token = ""  # place holder to start the loop
        while page_token is not None:
            response = self._client.files().list(q=q,
                                                 spaces='drive',
                                                 fields=self._get_fields_query_string(["id", "name", "parents"]),
                                                 pageToken=page_token).execute()
            result.extend(response.get("files", []))
            page_token = response.get("nextPageToken", None)

        if recursive and depth > 0:
            for file in result:
                children_id = file["id"]
                result.extend(self.list(id=children_id, recursive=True, depth=depth-1))

        if regex is not None:
            pattern = re.compile(regex)
            result = [f for f in result if pattern.match(f["name"])]

        return result

    @retry_on_out_of_quota()
    def delete(self, id: str, recursive: bool=False):
        """delete target file from google drive
        TODO: implement recursive delete

        :param id: id of target object.
        :param recursive: if True and target id represents a folder, remove all nested files and folders.
        :return: None
        """
        self._client.files().delete(fileId=id).execute()

    @retry_on_out_of_quota()
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

        folder = self._client.files().create(body=file_metadata, fields='id').execute()
        return folder.get("id")

    @retry_on_out_of_quota()
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

    @retry_on_out_of_quota()
    def get_name(self, id: str) -> str:
        """get the name of the Google drive object.

        :param id: id of the target Google drive object
        :return: name of the object
        """
        file = self._client.files().get(fileId=id).execute()
        return file['name']

    @retry_on_out_of_quota()
    def copy(self, id: str, name: str, parent_id: Optional[str]=None) -> str:
        """copy target file and give the new file specified name. return the id of the created file.

        :param id: target file to be copied.
        :param name: name of the new file.
        :param parent_id: the id of the folder where the new file is placed in. If None, the file will be placed in
            Google Drive root.
        :return: id of the created new file.
        """
        request = {"name": name}
        if parent_id is not None:
            request["parents"] = parent_id
        file = self._client.files().copy(fileId=id, body=request, fields='id').execute()
        return file.get("id")
