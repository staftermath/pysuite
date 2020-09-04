from typing import Optional
import random
import string
from datetime import datetime

import pytest
from pysuite import Drive

TEST_DRIVE_FOLDER_ID = "11dtprloqhpATi_awh8LAy_5xuCqTk1Ok"


def purge_temp_file(drive: Drive, prefix: str):
    temp_objects = drive.find(name_contains=prefix)
    for object in temp_objects:
        drive.delete(object["id"])


def random_string(length: int=8, seed: Optional[int]=None):
    if seed is None:
        seed = datetime.now().microsecond
    random.seed(seed)
    result = ''.join(random.choice(string.ascii_letters) for _ in range(length))
    return result


@pytest.fixture(scope="session")
def prefix():
    max_length = 26 # google api search for string longer than 26 char
    return random_string(max_length)+"_"
