import pytest
import uuid
from tests.test_auth import drive_auth
from pysuite import Drive

TEST_PREFIX = "_pysuite_test_tmp_"
TEST_DRIVE_FOLDER_ID = "11dtprloqhpATi_awh8LAy_5xuCqTk1Ok"


@pytest.fixture(scope="session")
def purge_temp_file(drive_auth):
    drive = Drive(service=drive_auth.get_service_client())
    test_suffix = "_"+str(uuid.uuid4())

    def purge():
        temp_objects = drive.list(id=TEST_DRIVE_FOLDER_ID, regex=f"^{TEST_PREFIX}.*^{test_suffix}", recursive=True, depth=5)
        for object in temp_objects:
            drive.delete(object["id"])

    purge()
    yield test_suffix
    purge()






