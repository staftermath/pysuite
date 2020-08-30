#!/bin/bash

set -e

TEST_DIR=$(pwd)/tests
pytest --verbose ${TEST_DIR}
