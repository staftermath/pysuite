#!/bin/bash

set -e

${CONDA}/envs/test/bin/coverage run -m pytest $GITHUB_WORKSPACE/tests
