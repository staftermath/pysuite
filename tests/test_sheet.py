import pytest

import pandas as pd
from pandas.testing import assert_frame_equal

from pysuite.sheet import Sheet
from tests.test_auth import sheet_auth

test_sheet_id = "1CNOH3o2Zz05mharkLXuwX72FpRka8-KFpIm9bEaja50"


@pytest.fixture()
def sheet(sheet_auth):
    return Sheet(client=sheet_auth.get_client())


@pytest.mark.parametrize(("dimension", "expected"),
                         [
                             ("ROWS",
                              [
                                  ['col1', 'col2', 'col3'],
                                  ['1', 'a', '10.15'],
                                  ['2', 'b', '20.2'],
                                  ['3', 'c', '0.59']
                              ]),
                             ("COLUMNS",
                             [
                                 ['col1', '1', '2', '3'],
                                 ['col2', 'a', 'b', 'c'],
                                 ['col3', '10.15', '20.2', '0.59']
                             ])
                         ])
def test_download_return_correct_values(sheet, dimension, expected):
    result = sheet.download(id=test_sheet_id,
                            range="download!A1:C",
                            dimension=dimension)
    assert result == expected


def test_upload_and_clear_change_sheet_value_correctly(sheet):
    range = "upload!A1:B"

    values = [["a", "b"], ["c", "d"], [1, 2]]
    sheet.upload(values=values, id=test_sheet_id, range=range)

    result = sheet.download(id=test_sheet_id, range=range)
    expected = [["a", "b"], ["c", "d"], ["1", "2"]]
    assert result == expected

    sheet.clear(id=test_sheet_id, range=range)

    result_cleared = sheet.download(id=test_sheet_id, range=range)
    assert result_cleared == []


@pytest.fixture()
def clear_sheet(sheet):
    def clear():
        sheet.clear(id=test_sheet_id, range="upload!A1:B")

    clear()
    yield
    clear()


@pytest.mark.parametrize(("header", "dtypes", "columns", "expected"),
                         [
                             (True, None, None, pd.DataFrame({
                                 "col1": ["1", "2", "3"],
                                 "col2": ["a", "b", "c"],
                                 "col3": ["10.15", "20.2", "0.59"]
                             })),
                             (False, None, ["new_col1", "new_col2", "new_col3"], pd.DataFrame({
                                 "new_col1": ["col1", "1", "2", "3"],
                                 "new_col2": ["col2", "a", "b", "c"],
                                 "new_col3": ["col3", "10.15", "20.2", "0.59"]
                             })),
                             (False, None, None, pd.DataFrame({
                                 0: ["col1", "1", "2", "3"],
                                 1: ["col2", "a", "b", "c"],
                                 2: ["col3", "10.15", "20.2", "0.59"]
                             })),
                             (True, {"col1": "int32", "col3": "float64"}, ["new_col1", "new_col2", "new_col3"],
                              pd.DataFrame({
                                 "col1": pd.Series([1, 2, 3], dtype="int32"),
                                 "col2": ["a", "b", "c"],
                                 "col3": [10.15, 20.2, 0.59]
                             })),
                         ])
def test_read_sheet_return_correct_values(sheet, header, dtypes, columns, expected):
    result = sheet.read_sheet(id=test_sheet_id, range="download!A1:C", header=header, dtypes=dtypes, columns=columns)
    assert_frame_equal(result, expected)


def test_to_sheet_update_values_correctly(sheet, clear_sheet):
    df = pd.DataFrame({
        "col1": ["a", None, "c"],
        "col2": [1, 2, 3]
    })
    range = "upload!A1:B"
    sheet.to_sheet(df, id=test_sheet_id, range=range)

    result = sheet.download(id=test_sheet_id, range=range)
    expected = [["col1", "col2"], ["a", "1"], ["", "2"], ["c", "3"]]
    assert result == expected
