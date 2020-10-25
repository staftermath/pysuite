#!/bin/bash

set -e

TEST_DIR=$(pwd)/tests
coverage -m pytest ${TEST_DIR}
