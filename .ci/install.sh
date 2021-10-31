#!/bin/bash

set -e

conda init bash
conda activate test
echo $(which python)
python $(pwd)/setup.py install
