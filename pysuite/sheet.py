"""implement api to access google sheet
"""
import logging

from googleapiclient.discovery import Resource

VALID_DIMENSION = {"COLUMNS", "ROWS"}


class Sheet:
    """provide api to operate google spreadsheet. An authenticated google api client is needed.
    """
    def __init__(self, client: Resource):
        self._client = client.spreadsheets()

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

        result = self._client.values().get(spreadsheetId=id,
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
        request = self._client.values().update(spreadsheetId=id,
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
        self._client.values().clear(spreadsheetId=id, range=range, body={}).execute()

    def read_sheet(self, id: str, range: str, header=True):
        """download the target sheet range into a pandas datafrme. this method will fail if pandas cannot be imported.

        :param id: id of the target spreadsheet
        :param range: range in the target spreadsheet.  for example, 'sheet!A1:D'. this means selecting from tab "sheet"
          and download column A to D and rows from 1 to the last row with non-empty values.
        :param header: whether first row is used as column names in the output dataframe.
        :return: a pandas dataframe containing target spreadsheet values.
        """
        try:
            import pandas as pd
        except ModuleNotFoundError as e:
            logging.critical("read_sheet() requires pandas.")
            raise e

        values = self.download(id=id, range=range)
        if values == []:
            return pd.DataFrame()

        columns = values.pop(0) if header else None
        df = pd.DataFrame(values, columns=columns)
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
