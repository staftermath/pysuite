import json

import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from googleapiclient.errors import HttpError

from pysuite.sheets import Sheets, get_col_counts_from_range, get_column_number
from tests.test_auth import sheets_auth, multi_auth
from tests.test_drive import drive, drive_auth
from tests.helper import purge_temp_file, prefix

test_sheet_id = "1CNOH3o2Zz05mharkLXuwX72FpRka8-KFpIm9bEaja50"
test_sheet_folder = "1qqFJ-OaV1rdPSeFtdaf6lUwFIpupOiiF"


@pytest.fixture(scope="session")
def sheets(sheets_auth):
    return Sheets(service=sheets_auth.get_service_client())


@pytest.mark.parametrize(("dimension", "range", "force_fill", "expected"),
                         [
                             ("ROWS", "download!A1:C", False,
                              [
                                  ['col1', 'col2', 'col3'],
                                  ['1', 'a', '10.15'],
                                  ['2', 'b', '20.2'],
                                  ['3', 'c', '0.59']
                              ]),
                             ("ROWS", "download!A1:C", True,
                              [
                                  ['col1', 'col2', 'col3'],
                                  ['1', 'a', '10.15'],
                                  ['2', 'b', '20.2'],
                                  ['3', 'c', '0.59']
                              ]),
                             ("ROWS", "download!A1:D", False,
                              [
                                  ['col1', 'col2', 'col3', 'col4'],
                                  ['1', 'a', '10.15'],
                                  ['2', 'b', '20.2'],
                                  ['3', 'c', '0.59']
                              ]),
                             ("ROWS", "download!A1:E", True,
                              [
                                  ['col1', 'col2', 'col3', 'col4', ''],
                                  ['1', 'a', '10.15', '', ''],
                                  ['2', 'b', '20.2', '', ''],
                                  ['3', 'c', '0.59', '', '']
                              ]),
                             ("COLUMNS", "download!A1:C", False,
                             [
                                 ['col1', '1', '2', '3'],
                                 ['col2', 'a', 'b', 'c'],
                                 ['col3', '10.15', '20.2', '0.59']
                             ]),
                             ("COLUMNS", "download!A1:D", True,
                             [
                                 ['col1', '1', '2', '3'],
                                 ['col2', 'a', 'b', 'c'],
                                 ['col3', '10.15', '20.2', '0.59'],
                                 ['col4']
                             ])
                         ])
def test_download_return_correct_values(sheets, dimension, range, force_fill, expected):
    result = sheets.download(id=test_sheet_id,
                             sheet_range=range,
                             dimension=dimension,
                             fill_row=force_fill)
    assert result == expected



@pytest.fixture(scope="module")
def clean_up_sheet_creation(sheets, prefix):
    title = f"{prefix}test_sheet"
    result = sheets.create_sheet(id=test_sheet_id, title=title)
    yield result, title
    sheets.delete_sheet(id=test_sheet_id, sheet_id=result["sheetId"])


def test_upload_and_clear_change_sheet_value_correctly(sheets, clean_up_sheet_creation):
    _, title = clean_up_sheet_creation
    sheet_range = f"{title}!A1:B"

    values = [["a", "b"], ["c", "d"], [1, 2]]
    sheets.upload(values=values, id=test_sheet_id, range=sheet_range)

    result = sheets.download(id=test_sheet_id, sheet_range=sheet_range)
    expected = [["a", "b"], ["c", "d"], ["1", "2"]]
    assert result == expected

    sheets.clear(id=test_sheet_id, sheet_range=sheet_range)

    result_cleared = sheets.download(id=test_sheet_id, sheet_range=sheet_range)
    assert result_cleared == []


@pytest.mark.parametrize(("header", "dtypes", "columns", "sheet_range", "fill_row", "expected"),
                         [
                             (True, None, None, "download!A1:C", False,
                              pd.DataFrame({
                                 "col1": ["1", "2", "3"],
                                 "col2": ["a", "b", "c"],
                                 "col3": ["10.15", "20.2", "0.59"]
                             })),
                             (True, None, None, "download!A1:F", True,
                              pd.DataFrame({
                                  "col1": ["1", "2", "3"],
                                  "col2": ["a", "b", "c"],
                                  "col3": ["10.15", "20.2", "0.59"],
                                  "col4": ["", "", ""],
                                  "__temp_col5": ["", "", ""],
                                  "__temp_col6": ["", "", ""],
                             })),
                             (False, None, ["new_col1", "new_col2", "new_col3"], "download!A1:C", True,
                              pd.DataFrame({
                                 "new_col1": ["col1", "1", "2", "3"],
                                 "new_col2": ["col2", "a", "b", "c"],
                                 "new_col3": ["col3", "10.15", "20.2", "0.59"]
                             })),
                             (False, None, None, "download!A1:C", False,
                              pd.DataFrame({
                                 0: ["col1", "1", "2", "3"],
                                 1: ["col2", "a", "b", "c"],
                                 2: ["col3", "10.15", "20.2", "0.59"]
                             })),
                             (True, {"col1": "int32", "col3": "float64"}, ["new_col1", "new_col2", "new_col3"],
                              "download!A1:C", False,
                              pd.DataFrame({
                                 "col1": pd.Series([1, 2, 3], dtype="int32"),
                                 "col2": ["a", "b", "c"],
                                 "col3": [10.15, 20.2, 0.59]
                             })),
                         ])
def test_read_sheet_return_correct_values(sheets, header, dtypes, columns, sheet_range, fill_row, expected):
    result = sheets.read_sheet(id=test_sheet_id,
                               sheet_range=sheet_range,
                               header=header,
                               dtypes=dtypes,
                               columns=columns,
                               fill_row=fill_row)
    assert_frame_equal(result, expected)


def test_to_sheet_update_values_correctly(sheets, clean_up_sheet_creation):
    _, title = clean_up_sheet_creation
    df = pd.DataFrame({
        "col1": ["a", None, "c"],
        "col2": [1, 2, 3]
    })
    sheet_range = f"{title}!A1:B"
    sheets.to_sheet(df, id=test_sheet_id, sheet_range=sheet_range)

    result = sheets.download(id=test_sheet_id, sheet_range=sheet_range)
    expected = [["col1", "col2"], ["a", "1"], ["", "2"], ["c", "3"]]
    assert result == expected


def test_multi_auth_token(multi_auth):
    sheets = Sheets(multi_auth.get_service_client("sheets"))
    result = sheets.read_sheet(id=test_sheet_id, sheet_range="download!A1:C")
    expected = pd.DataFrame({
        "col1": ["1", "2", "3"],
        "col2": ["a", "b", "c"],
        "col3": ["10.15", "20.2", "0.59"]
    })
    assert_frame_equal(result, expected)


@pytest.fixture()
def clean_up_created_spreadsheet(sheets, drive, prefix):
    id = sheets.create_spreadsheet(f"{prefix}test_sheet")
    yield id
    purge_temp_file(drive, prefix)


def test_create_spreadsheet_create_correctly(sheets, clean_up_created_spreadsheet):
    id = clean_up_created_spreadsheet
    result = sheets.download(id=id, sheet_range="Sheet1!A1:B2")
    assert result == []  # file created correctly


def test_create_sheet_create_correctly(clean_up_sheet_creation):
    result, expected_title = clean_up_sheet_creation
    assert result["title"] == expected_title


def test_rename_sheet_change_title_correctly(sheets, clean_up_sheet_creation, prefix):
    id = clean_up_sheet_creation[0]["sheetId"]
    new_title = f"{prefix}new_title"
    sheets.rename_sheet(id=test_sheet_id, sheet_id=id, title=new_title)
    try:
        sheets.download(id=test_sheet_id, sheet_range=f"{new_title}!A1:B2")
    except HttpError as e:
        error = json.loads(e.content.decode("ascii"))
        msg = error.get("error", dict()).get("message")
        if msg == 'Requested entity was not found.':
            pytest.fail(f"sheet not renamed properly. {e}")


@pytest.mark.parametrize(("col", "expected"),
                         [
                             ("A", 1),
                             ("C", 3),
                             ("AA", 27),
                             ("ZY", 701)
                         ])
def test_get_column_number_return_correct_values(col, expected):
    result = get_column_number(col)
    assert result == expected


@pytest.mark.parametrize(("range", "expected"),
                         [
                             ("test!A1:C", 3),
                             ("ok!A1:A", 1),
                             ("long!AA1:BZ", 52)
                         ])
def test_get_col_counts_from_range_returN_correct_values(range, expected):
    result = get_col_counts_from_range(range)
    assert result == expected
