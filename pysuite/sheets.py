"""Implements api to access google sheet.
"""
import logging
from typing import Optional, List
import re

from googleapiclient.discovery import build
from googleapiclient.discovery import Resource

from pysuite.auth import Authentication
from pysuite.utilities import retry_on_out_of_quota, MAX_RETRY_ATTRIBUTE, SLEEP_ATTRIBUTE

VALID_DIMENSION = {"COLUMNS", "ROWS"}


def _get_client(auth: Authentication, version: str) -> Resource:
    return build("sheets", version, credentials=auth.credential).spreadsheets()


class Sheets:
    """Provides api to operate google spreadsheet. An authenticated google api client is needed.

    :param auth: an authorized Google Spreadsheet service client.
    :param max_retry: max number of retry on quota exceeded error. if 0 or less, no retry will be attempted.
    :param sleep: base number of seconds between retries. the sleep time is exponentially increased after each retry.
    """

    def __init__(self, auth: Authentication, version: str = "v4", max_retry: int = 0, sleep: int = 5):
        self._client = _get_client(auth, version)
        setattr(self, MAX_RETRY_ATTRIBUTE, max_retry)
        setattr(self, SLEEP_ATTRIBUTE, sleep)

    @retry_on_out_of_quota()
    def download(self, id: str, sheet_range: str, dimension: str = "ROWS", fill_row: bool = False) -> list:
        """Downloads target sheet range by specified dimension.

        All entries will be considered as strings.

        :param id: id of the target spreadsheet.
        :param sheet_range: range in the target spreadsheet. for example, 'tab!A1:D'. this means selecting from tab
          "tab" and download column A to D and rows from 1 to the last row with non-empty values.
        :param dimension: "ROW" or "COLUMNS". If "ROWS", each entry in the output list would be one row in the
          spreadsheet. If "COLUMNS", each entry in the output list would be one column in the spreadsheet.
        :param fill_row: Whether force to return rows with desired number of columns. Google Sheet API ignores trailing
          empty cells by default. By setting this to True, empty strings will be filled in those ignored cells. This
          parameter only works when dimension is "ROWS".
        :return: content of target sheet range in a list of lists.
        """
        if dimension not in VALID_DIMENSION:
            raise ValueError(f"{dimension} is not a valid dimension. expecting {VALID_DIMENSION}.")

        result = self._client.values().get(spreadsheetId=id,
                                           range=sheet_range,
                                           majorDimension=dimension).execute()
        values = result.get('values', [])

        if fill_row and dimension == "ROWS":
            col_counts = get_col_counts_from_range(sheet_range)
            self._fill_rows(values, col_counts)

        return values

    @retry_on_out_of_quota()
    def upload(self, values: list, id: str, sheet_range: str) -> None:
        """Uploads a list of lists to target sheet range.

        All entries in the provided list must be serializable.

        :param values: a list of lists of objects that can be converted to str.
        :param id: id of the target spreadsheet.
        :param sheet_range: range in the target spreadsheet. for example, 'sheet!A1:D'. this means selecting from tab
          "sheet" and download column A to D and rows from 1 to the last row with non-empty values.
        :return: None
        """
        self.clear(id=id, sheet_range=sheet_range)
        body = {"values": values}
        logging.info(f"Updating sheet '{id}' range '{sheet_range}'")
        request = self._client.values().update(spreadsheetId=id,
                                               range=sheet_range,
                                               valueInputOption="RAW",
                                               body=body)
        result = request.execute()
        msg = f"{result.get('updatedRange')} has been updated ({result.get('updatedRows')} rows " \
              f"and {result.get('updatedColumns')} columns)"
        logging.info(msg)

    @retry_on_out_of_quota()
    def clear(self, id: str, sheet_range: str):
        """Removes content in the target sheet range.

        :param id: id of the target spreadsheet.
        :param sheet_range: range in the target spreadsheet.  for example, 'sheet!A1:D'. this means selecting from tab
          "sheet" and download column A to D and rows from 1 to the last row with non-empty values.
        :return: None
        """
        self._client.values().clear(spreadsheetId=id, range=sheet_range, body={}).execute()

    def read_sheet(self, id: str, sheet_range: str, header: bool = True, dtypes: Optional[dict] = None,
                   columns: Optional[list] = None, fill_row: bool = True):
        """Downloads the target sheet range into a pandas dataframe.

        This method will fail if pandas cannot be imported.

        :param id: id of the target spreadsheet.
        :param sheet_range: range in the target spreadsheet.  for example, 'sheet!A1:D'. this means selecting from tab
          "sheet" and download column A to D and rows from 1 to the last row with non-empty values.
        :param header: whether first row is used as column names in the output dataframe.
        :param dtypes: a mapping from column name to the type. if not None, type conversions will be applied to columns
          requested in the dictionary.
        :param columns: a list of column names. If not None and `header` is False, this will be used as columns of the
          output dataframe.
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

    def write_sheet(self, df, id: str, sheet_range: str):
        """Uploads pandas dataframe to target sheet range.

        The number of columns must fit the range. More columns or fewer columns will both raise exception. The data in
        the provided dataframe must be serializable.

        :param df: pandas dataframe to be uploaded.
        :type df: pandas.DataFrame.
        :param id: id of the target spreadsheet.
        :param sheet_range: range in the target spreadsheet.  for example, 'sheet!A1:D'. this means selecting from tab
          "sheet" and download column A to D and rows from 1 to the last row with non-empty values.
        :return: None
        """
        values = df.fillna('').values.tolist()
        values.insert(0, list(df.columns))  # insert column names to first row.
        self.upload(values, id=id, sheet_range=sheet_range)

    @retry_on_out_of_quota()
    def create_spreadsheet(self, name: str) -> str:
        """Creates a spreadsheet with requested name.

        :param name: name of the created sheet.
        :return: id of the spreadsheet.
        """
        file_metadata = {
            "properties": {"title": name}
        }
        response = self._client.create(body=file_metadata, fields="spreadsheetId").execute()
        return response.get("spreadsheetId")

    @retry_on_out_of_quota()
    def batch_update(self, id: str, body: dict):
        """Low level api used to submit a json body to make changes to the specified spreadsheet.

        :param id: id of the target spreadsheet.
        :param body: request json.
        :return: response from batch update.
        """
        response = self._client.batchUpdate(spreadsheetId=id, body=body).execute()
        return response

    def create_tab(self, id: str, title: str):
        """Creates a new tab with given name in the specified spreadsheet.

        :param id: id of the spreadsheet.
        :param title: title of the new tab.
        :return: a dictionary containing information about created sheet, such as sheet id, title, index.
        """
        request = {"requests": [{"addSheet": {"properties": {"title": title}}}]}
        response = self.batch_update(id=id, body=request)
        info = response.get("replies")[0]["addSheet"]["properties"]
        return info

    def delete_tab(self, id: str, tab_id: int):
        """Deletes the specified tab in the target spreadsheet.

        You can find tab_id from URL when you select the sheet in the spreadsheet after "gid=".

        :param id: id of spreadsheet.
        :param tab_id: id of tab.
        :return: None
        """
        request = {"requests": [{"deleteSheet": {"sheetId": tab_id}}]}
        self.batch_update(id=id, body=request)

    def rename_tab(self, id: str, tab_id: int, title: str):
        """Renames a tab in target spreadsheet to the new title.

        :param id: id of the target spreadsheet.
        :param tab_id: id of the tab.
        :param title: new title of the sheet.
        :return: None
        """
        request = {"requests": [
            {"updateSheetProperties": {"properties": {"sheetId": tab_id, "title": title}, "fields": "title"}}
        ]
        }
        self.batch_update(id=id, body=request)

    def _fill_rows(self, rows: List[list], col_counts: int):
        for row in rows:
            if len(row) < col_counts:
                row.extend(['']*(col_counts - len(row)))


def get_column_number(col: str) -> int:
    """Convert spreadsheet column numbers to integer.

    :example:

    >>> get_column_number('A')  # 1
    >>> get_column_number('AA') # 27
    >>> get_column_number('ZY') # 701

    :param col: upper case spreadsheet column
    :return: index of the column starting from 1.
    """
    result = 0
    l = len(col)
    for i in range(l):
        result += (ord(col[l-i-1]) - 64) * (26 ** i)

    return result


def get_col_counts_from_range(sheet_range: str) -> int:
    """Calculate the number of columns in the given range.

    :example:

    >>> get_col_counts_from_range("test!A1:A")  # 1
    >>> get_col_counts_from_range("test!A1:D")  # 4
    >>> get_col_counts_from_range("test!AA2:AZ")  # 26

    :param sheet_range: a string representation of sheet range. For example, "test_sheet!A1:D"
    :return: the number of columns contained in the range.
    """
    columns = sheet_range.upper().split("!")[1]  # get the columns in letter, such as "A1:D"
    from_column, to_column = columns.split(":")
    pattern = re.compile("^([A-Z]+)", re.IGNORECASE)
    from_column = pattern.search(from_column).group(0)
    to_column = pattern.search(to_column).group(0)
    counts = get_column_number(to_column) - get_column_number(from_column) + 1
    return counts
