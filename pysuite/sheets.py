"""implement api to access google sheet
"""
import logging
from typing import Optional, List

from googleapiclient.discovery import Resource

from pysuite.utilities import retry_on_out_of_quota, MAX_RETRY_ATTRIBUTE, SLEEP_ATTRIBUTE, get_col_counts_from_range

VALID_DIMENSION = {"COLUMNS", "ROWS"}


class Sheets:
    """provide api to operate google spreadsheet. An authenticated google api client is needed.

    :param service: an authorized Google Spreadsheet service client.
    :param max_retry: max number of retry on quota exceeded error. if 0 or less, no retry will be attempted.
    :param sleep: base number of seconds between retries. the sleep time is exponentially increased after each retry.
    """

    def __init__(self, service: Resource, max_retry: int=0, sleep: int=5):
        self._service = service.spreadsheets()
        setattr(self, MAX_RETRY_ATTRIBUTE, max_retry)
        setattr(self, SLEEP_ATTRIBUTE, sleep)

    @retry_on_out_of_quota()
    def download(self, id: str, sheet_range: str, dimension: str= "ROWS", fill_row: bool=False) -> list:
        """download target sheet range by specified dimension. All entries will be considered as strings.

        :param id: id of the target spreadsheet.
        :param sheet_range: range in the target spreadsheet. for example, 'sheet!A1:D'. this means selecting from tab "sheet"
          and download column A to D and rows from 1 to the last row with non-empty values.
        :param dimension: "ROW" or "COLUMNS". If "ROWS", each entry in the output list would be one row in the
          spreadsheet. If "COLUMNS", each entry in the output list would be one column in the spreadsheet.
        :param fill_row: Whether force to return rows with desired number of columns. Google Sheet API ignores trailing
          empty cells by default. By setting this to True, empty strings will be filled in those ignored cells. This
          parameter only works when dimension is "ROWS".
        :return: content of target sheet range in a list of lists.
        """
        if dimension not in VALID_DIMENSION:
            raise ValueError(f"{dimension} is not a valid dimension. expecting {VALID_DIMENSION}.")

        result = self._service.values().get(spreadsheetId=id,
                                            range=sheet_range,
                                            majorDimension=dimension).execute()
        values = result.get('values', [])

        if fill_row and dimension == "ROWS":
            col_counts = get_col_counts_from_range(sheet_range)
            self._fill_rows(values, col_counts)

        return values

    @retry_on_out_of_quota()
    def upload(self, values: list, id: str, range: str) -> None:
        """Upload a list of lists to target sheet range. All entries in the provided list must be serializable.

        :param values: a list of lists of objects that can be converted to str.
        :param id: id of the target spreadsheet
        :param range: range in the target spreadsheet. for example, 'sheet!A1:D'. this means selecting from tab "sheet"
          and download column A to D and rows from 1 to the last row with non-empty values.
        :return: None
        """
        self.clear(id=id, sheet_range=range)
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

    @retry_on_out_of_quota()
    def clear(self, id: str, sheet_range: str):
        """remove content in the target sheet range.

        :param id: id of the target spreadsheet
        :param sheet_range: range in the target spreadsheet.  for example, 'sheet!A1:D'. this means selecting from tab "sheet"
          and download column A to D and rows from 1 to the last row with non-empty values.
        :return: None
        """
        self._service.values().clear(spreadsheetId=id, range=sheet_range, body={}).execute()

    def read_sheet(self, id: str, sheet_range: str, header=True, dtypes: Optional[dict]=None,
                   columns: Optional[list]=None, fill_row: bool=True):
        """download the target sheet range into a pandas dataframe. this method will fail if pandas cannot be imported.

        :param id: id of the target spreadsheet
        :param sheet_range: range in the target spreadsheet.  for example, 'sheet!A1:D'. this means selecting from tab "sheet"
          and download column A to D and rows from 1 to the last row with non-empty values.
        :param header: whether first row is used as column names in the output dataframe.
        :param dtypes: a mapping from column name to the type. if not None, type conversions will be applied to columns
          requested in the dictionary.
        :param columns: a list of column names. If not None and `header` is False, this will be used as columns of the
          output dataframe
        :param fill_row: Whether attempt to fill the trailing empty cell with empty strings. This prevents errors when
          the trailing cells in some rows are empty in the sheet. When header is True, this will attempt to fill the
          missing header with _col{i}, where i is the index of the column (starting from 1).
        :return: a pandas dataframe containing target spreadsheet values.
        """
        try:
            import pandas as pd
        except ModuleNotFoundError as e:
            logging.critical("read_sheet() requires pandas.")
            raise e

        if dtypes is not None and not isinstance(dtypes, dict):
            raise TypeError(f"dtypes must be dictionary. got {type(dtypes)}")

        values = self.download(id=id, sheet_range=sheet_range, fill_row=fill_row)
        if values == []:
            return pd.DataFrame()

        if header:
            columns = values.pop(0)
            if fill_row:
                for i in range(len(columns)):
                    if columns[i] == "":
                        columns[i] = f"_col{i+1}"

        df = pd.DataFrame(values, columns=columns)

        if dtypes is not None:
            for col, type in dtypes.items():
                df[col] = df[col].astype(type)

        return df

    def to_sheet(self, df, id: str, sheet_range: str):
        """Upload pandas dataframe to target sheet range. The number of columns must fit the range. More columns or
        fewer columns will both raise exception. The data in the provided dataframe must be serializable.

        :param df: pandas dataframe to be uploaded
        :type df: pandas.DataFrame
        :param id: id of the target spreadsheet
        :param sheet_range: range in the target spreadsheet.  for example, 'sheet!A1:D'. this means selecting from tab "sheet"
          and download column A to D and rows from 1 to the last row with non-empty values.
        :return: None
        """
        values = df.fillna('').values.tolist()
        values.insert(0, list(df.columns))  # insert column names to first row.
        self.upload(values, id=id, range=sheet_range)

    @retry_on_out_of_quota()
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

    @retry_on_out_of_quota()
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

    def _fill_rows(self, rows: List[list], col_counts: int):
        for row in rows:
            if len(row) < col_counts:
                row.extend(['']*(col_counts - len(row)))
