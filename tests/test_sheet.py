import pytest

import pandas as pd
from pandas.testing import assert_frame_equal

from pysuite.sheets import Sheets
from tests.test_auth import sheets_auth, multi_auth
from tests.test_drive import drive, drive_auth
from tests.helper import TEST_PREFIX, purge_temp_file

test_sheet_id = "1CNOH3o2Zz05mharkLXuwX72FpRka8-KFpIm9bEaja50"
test_sheet_folder = "1qqFJ-OaV1rdPSeFtdaf6lUwFIpupOiiF"


@pytest.fixture()
def sheets(sheets_auth):
    return Sheets(service=sheets_auth.get_service_client())


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
def test_download_return_correct_values(sheets, dimension, expected):
    result = sheets.download(id=test_sheet_id,
                             range="download!A1:C",
                             dimension=dimension)
    assert result == expected


def test_upload_and_clear_change_sheet_value_correctly(sheets):
    range = "upload!A1:B"

    values = [["a", "b"], ["c", "d"], [1, 2]]
    sheets.upload(values=values, id=test_sheet_id, range=range)

    result = sheets.download(id=test_sheet_id, range=range)
    expected = [["a", "b"], ["c", "d"], ["1", "2"]]
    assert result == expected

    sheets.clear(id=test_sheet_id, range=range)

    result_cleared = sheets.download(id=test_sheet_id, range=range)
    assert result_cleared == []


@pytest.fixture()
def clear_sheet(sheets):
    def clear():
        sheets.clear(id=test_sheet_id, range="upload!A1:B")

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
def test_read_sheet_return_correct_values(sheets, header, dtypes, columns, expected):
    result = sheets.read_sheet(id=test_sheet_id, range="download!A1:C", header=header, dtypes=dtypes, columns=columns)
    assert_frame_equal(result, expected)


def test_to_sheet_update_values_correctly(sheets, clear_sheet):
    df = pd.DataFrame({
        "col1": ["a", None, "c"],
        "col2": [1, 2, 3]
    })
    range = "upload!A1:B"
    sheets.to_sheet(df, id=test_sheet_id, range=range)

    result = sheets.download(id=test_sheet_id, range=range)
    expected = [["col1", "col2"], ["a", "1"], ["", "2"], ["c", "3"]]
    assert result == expected


def test_multi_auth_token(multi_auth):
    sheets = Sheets(multi_auth.get_service_client("sheets"))
    result = sheets.read_sheet(id=test_sheet_id, range="download!A1:C")
    expected = pd.DataFrame({
        "col1": ["1", "2", "3"],
        "col2": ["a", "b", "c"],
        "col3": ["10.15", "20.2", "0.59"]
    })
    assert_frame_equal(result, expected)


@pytest.fixture()
def clean_up_created_spreadsheet(sheets, drive, purge_temp_file):
    suffix = purge_temp_file
    id = sheets.create_spreadsheet(f"{TEST_PREFIX}test_sheet{suffix}")
    yield id
    drive.delete(id)


def test_create_spreadsheet_create_correctly(sheets, clean_up_created_spreadsheet):
    id = clean_up_created_spreadsheet
    result = sheets.download(id=id, range="Sheet1!A1:B2")
    assert result == []  # file created correctly
