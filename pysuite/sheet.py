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

    def upload(self, values: list, id: str, range: str):
        self.clear(id=id, range=range)
        body = {"values": values}
        logging.info(f"Updating sheet '{id}' range '{range}'")
        request = self._client.values().update(spreadsheetId=id,
                                              range=range,
                                              valueInputOption="RAW",
                                              body=body)
        result = request.execute()
        msg = f"{result.get('updatedRange')} has been updated ({result.get('updatedRows')} rows " \
              f"and {result.get('updatedColumns')} columns)"
        logging.info(msg)

    def clear(self, id: str, range: str):
        self._client.values().clear(spreadsheetId=id, range=range, body={}).execute()

    def read_sheet(self, id: str, range: str):
        pass

    def to_sheet(self, id: str, range: str):
        pass
