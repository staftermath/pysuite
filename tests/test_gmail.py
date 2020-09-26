import pytest

from pysuite.gmail import GMail

from tests.helper import resource_folder
from tests.test_auth import gmail_auth, multi_auth


@pytest.fixture()
def gmail(gmail_auth):
    return GMail(service=gmail_auth.get_service_client())


@pytest.mark.parametrize(("body", "local_files", "gdrive_ids"),
                         [
                             (None, None, None),
                             ("with only local file attachment", [resource_folder / "gmail_attachment.txt"], None),
                             ("with a list of local files", [resource_folder / "gmail_attachment.txt",
                              resource_folder / "gmail_attachment_2.txt"], None),
                             ("with both local file and gdrive files",
                              [resource_folder / "gmail_attachment.txt"],
                              ["1-zIfn0kUcK6KI9PfZLXu6uCt01ZSOTOZ",
                               "1_wlzJVoAKVrndIfEOfSpzNe2NyPX9L2M"]),
                         ])
def test_compose_create_correct_response(gmail, body, local_files, gdrive_ids):
    response = gmail.compose(body=body, sender="pysuite.test@gmail.com",
                             subject="pysuite test", to=["pysuite.test@gmail.com"],
                             local_files=local_files,
                             gdrive_ids=gdrive_ids)
    assert response['labelIds'] == ['UNREAD', 'SENT', 'INBOX']
