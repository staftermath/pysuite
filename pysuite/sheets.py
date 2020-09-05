"""implement api to access google sheet
"""
import logging
from typing import Optional

from googleapiclient.discovery import Resource

VALID_DIMENSION = {"COLUMNS", "ROWS"}


class Sheets:
    """provide api to operate google spreadsheet. An authenticated google api client is needed.
    """
    def __init__(self, service: Resource):
        self._service = service.spreadsheets()

    def download(self, id: str, range: str, dimension: str="ROWS") -> list:
        """download target sheet range by specified dimension. All entries will be considered as strings.

        :param id: id of the target spreadsheet.
        :param range: range in the target spreadsheet. for example, 'sheet!A1:D'. this means selecting from tab "sheet"
          and download column A to D and rows from 1 to the last row with non-empty values.
        :param dimension: "ROW" or "COLUMNS". If "ROWS", each entry in the output list would be one row in the
          spreadsheet. If "COLUMNS", each entry in the output list would be one column in the spreadsheet.
        :return: content of target sheet range in a list of lists.
        """
        if dimension not in VALID_DIMENSION:
            raise ValueError(f"{dimension} is not a valid dimension. expecting {VALID_DIMENSION}.")

        result = self._service.values().get(spreadsheetId=id,
                                            range=range,
                                            majorDimension=dimension).execute()
        values = result.get('values', [])
        return values

    def upload(self, values: list, id: str, range: str) -> None:
        """upload a list of lists to target sheet range.

        :param values: a list of lists of objects that can be converted to str.
        :param id: id of the target spreadsheet
        :param range: range in the target spreadsheet. for example, 'sheet!A1:D'. this means selecting from tab "sheet"
          and download column A to D and rows from 1 to the last row with non-empty values.
        :return: None
        """
        self.clear(id=id, range=range)
        body = {"values": values}
        logging.info(f"Updating sheet '{id}' range '{range}'")
        request = self._service.values().update(spreadsheetId=id,
                                                range=range,
                                                valueInputOption="RAW",
                                                body=body)
        result = request.execute()
        msg = f"{result.get('updatedRange')} has been updated ({result.get('updatedRows')} rows " \
              f"and {result.get('updatedColumns')} columns)"
        logging.info(msg)

    def clear(self, id: str, range: str):
        """remove content in the target sheet range.

        :param id: id of the target spreadsheet
        :param range: range in the target spreadsheet.  for example, 'sheet!A1:D'. this means selecting from tab "sheet"
          and download column A to D and rows from 1 to the last row with non-empty values.
        :return: None
        """
        self._service.values().clear(spreadsheetId=id, range=range, body={}).execute()

    def read_sheet(self, id: str, range: str, header=True, dtypes: Optional[dict]=None, columns: Optional[list]=None):
        """download the target sheet range into a pandas datafrme. this method will fail if pandas cannot be imported.

        :param id: id of the target spreadsheet
        :param range: range in the target spreadsheet.  for example, 'sheet!A1:D'. this means selecting from tab "sheet"
          and download column A to D and rows from 1 to the last row with non-empty values.
        :param header: whether first row is used as column names in the output dataframe.
        :param dtypes: a mapping from column name to the type. if not None, type conversions will be applied to columns
          requested in the dictionary.
        :param columns: a list of column names. If not None and `header` is False, this will be used as columns of the
          output dataframe
        :return: a pandas dataframe containing target spreadsheet values.
        """
        try:
            import pandas as pd
        except ModuleNotFoundError as e:
            logging.critical("read_sheet() requires pandas.")
            raise e

        if dtypes is not None and not isinstance(dtypes, dict):
            raise TypeError(f"dtypes must be dictionary. got {type(dtypes)}")

        values = self.download(id=id, range=range)
        if values == []:
            return pd.DataFrame()

        columns = values.pop(0) if header else columns
        df = pd.DataFrame(values, columns=columns)

        if dtypes is not None:
            for col, type in dtypes.items():
                df[col] = df[col].astype(type)

        return df

    def to_sheet(self, df, id: str, range: str):
        """upload pandas dataframe to target sheet range. the number of columns must fit the range. more columns or
        fewer columns will both raise exception.

        :param df: pandas dataframe to be uploaded
        :type df: pandas.DataFrame
        :param id: id of the target spreadsheet
        :param range: range in the target spreadsheet.  for example, 'sheet!A1:D'. this means selecting from tab "sheet"
          and download column A to D and rows from 1 to the last row with non-empty values.
        :return: None
        """
        values = df.fillna('').values.tolist()
        values.insert(0, list(df.columns))
        self.upload(values, id=id, range=range)

    def create_spreadsheet(self, name: str) -> str:
        """create a spreadsheet with requested name.

        :param name: name of the created sheet.
        :return: id of the spreadsheet
        """
        file_metadata = {
            "properties": {"title": name}
        }
        response = self._service.create(body=file_metadata, fields="spreadsheetId").execute()
        return response.get("spreadsheetId")

    def batch_update(self, id: str, body: dict):
        """low level api used to submit a json body to make changes to the specified spreadsheet.

        :param id: id of the target spreadsheet
        :param body: request json
        :return: response from batch upate
        """
        response = self._service.batchUpdate(spreadsheetId=id, body=body).execute()
        return response

    def create_sheet(self, id: str, title: str):
        """create a new sheet with given name in the specified spreadsheet.

        :param id: id of the spreadsheet
        :param title: title of the new sheet
        :return: a dictionary containing information about created sheet, such as sheet id, title, index.
        """
        request = {"requests": [{"addSheet": {"properties": {"title": title}}}]}
        response = self.batch_update(id=id, body=request)
        info = response.get("replies")[0]["addSheet"]["properties"]
        return info

    def delete_sheet(self, id: str, sheet_id: int):
        """delete the specified sheet in the target spreadsheet. You can find sheet_id from URL when you select the
        sheet in the spreadsheet after "gid="

        :param id: id of spreadsheet.
        :param sheet_id: id of sheet
        :return: None
        """
        request = {"requests": [{"deleteSheet": {"sheetId": sheet_id}}]}
        self.batch_update(id=id, body=request)

    def rename_sheet(self, id: str, sheet_id: int, title: str):
        """rename a sheet in target spreadsheet to the new title.

        :param id: id of the target spreadsheet
        :param sheet_id: id of the sheet
        :param title: new title of the sheet
        :return: None
        """
        request = {"requests": [
            {"updateSheetProperties": {"properties": {"sheetId": sheet_id, "title": title}, "fields": "title"}}
        ]
        }
        self.batch_update(id=id, body=request)
