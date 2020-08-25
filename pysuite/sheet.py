import logging
from pathlib import PosixPath, Path
from typing import Union, Optional, List

from googleapiclient.discovery import Resource

VALID_DIMENSION = {"COLUMNS", "ROWS"}


class Sheet:

    def __init__(self, client: Resource):
        self._client = client.spreadsheets()

    def download(self, id: str, range: str, dimension: str="ROWS"):
        if dimension not in VALID_DIMENSION:
            raise ValueError(f"{dimension} is not a valid dimension. expecting {VALID_DIMENSION}.")

        result = self._client.values().get(spreadsheetId=id,
                                           range=range,
                                           majorDimension=dimension).execute()
        values = result.get('values', [])
        return values

    def upload(self, id: str, range: str):
        pass

    def read_sheet(self, id: str, range: str):
        pass

    def to_sheet(self, id: str, range: str):
        pass
