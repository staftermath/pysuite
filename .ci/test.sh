#!/bin/bash

set -e

${CONDA}/envs/test/bin/pytest $GITHUB_WORKSPACE/tests --cov=./ --cov-report=xml
