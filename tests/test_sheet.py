import pytest
from pathlib import Path

from pysuite.sheet import Sheet
from googleapiclient.errors import HttpError
from tests.test_auth import sheet_client

test_sheet_id = "1CNOH3o2Zz05mharkLXuwX72FpRka8-KFpIm9bEaja50"


@pytest.fixture()
def sheet(sheet_client):
    return Sheet(client=sheet_client.get_client())


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

