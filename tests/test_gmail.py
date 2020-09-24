import pytest

from pysuite.gmail import GMail

from tests.helper import resource_folder
from tests.test_auth import gmail_auth, multi_auth


@pytest.fixture()
def gmail(gmail_auth):
    return GMail(service=gmail_auth.get_service_client())


@pytest.mark.parametrize(("local_files"),
                         [
                             None,
                             [resource_folder / "gmail_attachment.txt"],
                             [resource_folder / "gmail_attachment.txt",
                              resource_folder / "gmail_attachment_2.txt"]
                         ])
def test_compose_create_correct_response(gmail, local_files):
    response = gmail.compose(body="hello world", sender="pysuite.test@gmail.com",
                             subject="pysuite test", to=["pysuite.test@gmail.com"],
                             local_files=local_files)
    assert response['labelIds'] == ['UNREAD', 'SENT', 'INBOX']
