#!/bin/bash

set -e

TEST_DIR=$(pwd)/tests
coverage run -m pytest ${TEST_DIR}
