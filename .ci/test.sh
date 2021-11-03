#!/bin/bash

set -e

${CONDA}/envs/test/bin/pytest $GITHUB_WORKSPACE/tests --cov=$GITHUB_WORKSPACE/pysuite --cov-report=xml
