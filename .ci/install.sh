#!/bin/bash

set -e

conda activate test
echo $(which python)
python $(pwd)/setup.py install
