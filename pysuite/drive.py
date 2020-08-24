from pathlib import PosixPath
from typing import Union, Optional, List

from googleapiclient.discovery import Resource


class Drive:

    def __init__(self, client: Resource):
        self._client = client

    def download(self, id: str, to_file: Union[str, PosixPath]):
        pass

    def upload(self, from_file: Union[str, PosixPath], name: Optional[str]=None, mimetype: Optional[str]=None,
               parent_ids: Optional[List[str]]=None) -> str:
        pass

    def update(self, id: str, from_file: Union[str, PosixPath]):
        pass

    def get_id(self, name: str, parent_id: Optional[str]=None):
        pass

    def list(self, id: str):
        pass

    def delete(self, id: str, recursive: bool=False):
        pass

    def create_folder(self, name: str, parent_ids: Optional[list]=None):
        pass

    def modify_sharing(self, id: str, emails: List[str], role: str="reader", notify=True):
        pass
