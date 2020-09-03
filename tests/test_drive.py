import pytest
from pathlib import Path

from pysuite.drive import Drive
from googleapiclient.errors import HttpError

from tests.test_auth import drive_auth, multi_auth
from tests.helper import TEST_DRIVE_FOLDER_ID, purge_temp_file, prefix


@pytest.fixture()
def drive(drive_auth):
    return Drive(service=drive_auth.get_service_client())


def test_get_id_return_correct_value(drive):
    result = drive.get_id("drive_test_file")
    expected = "1-zIfn0kUcK6KI9PfZLXu6uCt01ZSOTOZ"
    assert result == expected


def test_get_id_for_non_unique_name_raise_runtime_error(drive):
    with pytest.raises(RuntimeError):
        drive.get_id("drive_test_non_unique_file")


def test_get_id_in_parent_id_return_correct_value(drive):
    result = drive.get_id("drive_test_non_unique_file", parent_id="1qcfrD7RqZWwPVO9C7tbL1PNRa2aUQlF8")
    expected = "12K7eoK6M3MNOcNQmfMFjL1mCz8A_-St8"
    assert result == expected


def test_download_create_file_correctly(drive, tmpdir):
    download_file = Path(tmpdir.join("test_download.txt"))
    drive.download(id="1-zIfn0kUcK6KI9PfZLXu6uCt01ZSOTOZ",
                   to_file=download_file)

    with open(download_file, 'r') as f:
        result = [l.strip() for l in f.readlines()]

    assert result == ["hello", "world"]


@pytest.fixture()
def clean_up_upload_and_delete(prefix, drive):
    yield prefix
    purge_temp_file(drive=drive, prefix=prefix)


def test_upload_and_delete_correctly_create_and_remove_file(drive, prefix, tmpdir):
    file_to_upload = Path(tmpdir.join("test_upload_file"))
    file_to_upload.write_text("hello world")
    id = drive.upload(from_file=file_to_upload, name=f"{prefix}test_file",
                      parent_ids=["1_p0khJ5euUDbZhWiXbN5fefozKMD28yZ"])

    download_file = Path(tmpdir.join("test_downloaded_file"))
    drive.download(id=id, to_file=download_file)

    with open(download_file, 'r') as f:
        result = [l.strip() for l in f.readlines()]

    assert result == ["hello world"]

    drive.delete(id=id)

    with pytest.raises(HttpError):
        drive.download(id=id, to_file=download_file)


@pytest.fixture()
def clean_up_update(drive, tmpdir, prefix):
    file_to_upload = Path(tmpdir.join("test_upload_file"))
    file_to_upload.write_text("hello world")
    id = drive.upload(from_file=file_to_upload, name=f"{prefix}drive_test_file",
                      parent_ids=[TEST_DRIVE_FOLDER_ID])
    yield id
    purge_temp_file(drive, prefix)


def test_update_change_file_content_correctly(drive, clean_up_update, tmpdir):
    file_to_update = Path(tmpdir.join("test_upload_file"))
    file_to_update.write_text("the world has changed")
    id = clean_up_update
    drive.update(id=id, from_file=file_to_update)

    downloaded_file = Path(tmpdir.join("test_update_file_downloaded"))
    drive.download(id=id, to_file=downloaded_file)
    with open(downloaded_file, 'r') as f:
        result = [l.strip() for l in f.readlines()]

    assert result == ["the world has changed"]


no_recursive = [
    {'id': '1cYHUzVPAb3ibvSzH34fktzpr9SXtPJRP', 'name': 'children_folder',
     'parents': ['1R5zuuDSzR9BW3pOJmwhYEIILQ23p0kYv']},
    {'id': '1bR7LoLo_BBjHyTsDk4y-27wyBk_6K6-t', 'name': 'c', "parents": ["1R5zuuDSzR9BW3pOJmwhYEIILQ23p0kYv"]},
    {'id': '1tyZqvCeoiA5OvrGuHoygiy73qrNoLRdL', 'name': 'b', "parents": ["1R5zuuDSzR9BW3pOJmwhYEIILQ23p0kYv"]},
    {'id': '1erVdsBfgNVpMEWRhp0o-DDUfC26O7luO', 'name': 'a', "parents": ["1R5zuuDSzR9BW3pOJmwhYEIILQ23p0kYv"]},
]

sub_list_no_regex = [
    {'id': '1XWqT23KeaQIeUrRpl-gEoEHdJdVuRCnx', 'name': 'd', 'parents': ['1cYHUzVPAb3ibvSzH34fktzpr9SXtPJRP']},
    {'id': '1pezOWnHDfVRd7YjgULZhD1nGWEPmxNhE', 'name': 'e1', 'parents': ['1cYHUzVPAb3ibvSzH34fktzpr9SXtPJRP']}
]

sub_list_filtered_by_regex = [
    {'id': '1XWqT23KeaQIeUrRpl-gEoEHdJdVuRCnx', 'name': 'd', 'parents': ['1cYHUzVPAb3ibvSzH34fktzpr9SXtPJRP']},
]


@pytest.mark.parametrize(("recursive", "regex", "expected"),
                         [
                             [False, None, no_recursive],
                             [True, None, no_recursive+sub_list_no_regex],
                             [True, "^[_a-zA-Z]*$", no_recursive+sub_list_filtered_by_regex]
                         ])
def test_list_return_correct_values(drive, recursive, regex, expected):
    result = drive.list(id="1R5zuuDSzR9BW3pOJmwhYEIILQ23p0kYv", recursive=recursive, regex=regex)
    assert sorted(result, key=lambda x: x["name"]) == sorted(expected, key=lambda x: x["name"])


def test_get_name_return_correct_value(drive):
    result = drive.get_name("1-zIfn0kUcK6KI9PfZLXu6uCt01ZSOTOZ")
    expected = "drive_test_file"
    assert result == expected


@pytest.fixture()
def clean_folder(drive, prefix):
    folder_id = "1iUzQwHtr3KE_jR3AGo2-Qjq_5v99eh5u"
    yield folder_id

    purge_temp_file(drive, prefix)


def test_create_folder_correctly(drive, clean_folder, prefix):
    folder_id = "1iUzQwHtr3KE_jR3AGo2-Qjq_5v99eh5u"
    expected = f"{prefix}create_folder"
    id = drive.create_folder(expected, parent_ids=[folder_id])
    result = drive.get_name(id)
    assert result == expected


def test_multi_auth_token(multi_auth):
    drive = Drive(multi_auth.get_service_client("drive"))
    result = drive.get_name("1-zIfn0kUcK6KI9PfZLXu6uCt01ZSOTOZ")
    expected = "drive_test_file"
    assert result == expected


@pytest.mark.parametrize(("contains", "not_contains", "expected"),
                         [
                             ("positive", None,
                              [{'id': '1MmgjCLivbb-EPkHplTuNIDgj1Ma9wQw4', 'name': 'positive_c_negative'},
                               {'id': '1pkokaiJP9d0V_eaY4_H_Du4g5AfCG5Er', 'name': 'positive_b'},
                               {'id': '1S_QfcIiBaxhoAnq1csciQuEr4wz4mYh-', 'name': 'positive_a'}]),
                             ("a", None,
                              [{'id': '17tXdw1kQHuxdrcbkKYz81862UP2s6x2a', 'name': 'aa'}]),
                             ("positive", "negative",
                              [{'id': '1pkokaiJP9d0V_eaY4_H_Du4g5AfCG5Er', 'name': 'positive_b'},
                               {'id': '1S_QfcIiBaxhoAnq1csciQuEr4wz4mYh-', 'name': 'positive_a'}]),
                             (None, "negative",
                              [{'id': '17tXdw1kQHuxdrcbkKYz81862UP2s6x2a', 'name': 'aa'},
                               {'id': '1pkokaiJP9d0V_eaY4_H_Du4g5AfCG5Er', 'name': 'positive_b'},
                               {'id': '1S_QfcIiBaxhoAnq1csciQuEr4wz4mYh-', 'name': 'positive_a'}]
)
                         ])
def test_find_return_correct_values(drive, contains, not_contains, expected):
    result = drive.find(name_contains=contains, name_not_contains=not_contains, parent_id="1LOeJyQpD8tqXF5sm6cqpmOPcTBEg6NaE")
    assert sorted(result, key=lambda x: x['name']) == sorted(expected, key=lambda x: x['name'])
