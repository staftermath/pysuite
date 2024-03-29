import pytest

from pysuite.gmail import GMail

from tests.helper import resource_folder
from tests.test_auth import auth_fixture


@pytest.fixture()
def gmail(auth_fixture):
    return GMail(auth=auth_fixture)


@pytest.mark.parametrize(("body", "to", "local_files", "gdrive_ids"),
                         [
                             (None, "pysuite.test@gmail.com", None, None),
                             ("with only local file attachment", ["pysuite.test@gmail.com"],
                              [resource_folder / "gmail_attachment.txt"], None),
                             ("with a list of local files", ["pysuite.test@gmail.com"],
                              [resource_folder / "gmail_attachment.txt",
                              resource_folder / "gmail_attachment_2.txt"], None),
                             ("with both local file and gdrive files",
                              ["pysuite.test@gmail.com"],
                              [resource_folder / "gmail_attachment.txt"],
                              ["1-zIfn0kUcK6KI9PfZLXu6uCt01ZSOTOZ",
                               "1_wlzJVoAKVrndIfEOfSpzNe2NyPX9L2M"]),
                         ])
def test_compose_create_correct_response(gmail, body, to, local_files, gdrive_ids):
    response = gmail.compose(body=body, sender="pysuite.test@gmail.com",
                             subject="pysuite test", to=to,
                             local_files=local_files,
                             gdrive_ids=gdrive_ids)
    assert response['labelIds'] == ['UNREAD', 'SENT', 'INBOX']
