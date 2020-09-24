import pytest

from pysuite.gmail import GMail

from tests.test_auth import gmail_auth, multi_auth


@pytest.fixture()
def gmail(gmail_auth):
    return GMail(service=gmail_auth.get_service_client())


def test_compose_create_correct_response(gmail):
    response = gmail.compose(body="hello world", sender="pysuite.test@gmail.com", to=["pysuite.test@gmail.com"])
    assert response['labelIds'] == ['UNREAD', 'SENT', 'INBOX']
