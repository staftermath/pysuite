#!/bin/bash

set -e

echo $(which python)
source activate test
echo $(which python)
python $(pwd)/setup.py install
