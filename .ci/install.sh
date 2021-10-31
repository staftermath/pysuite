#!/bin/bash

set -e

conda activate test
python $(pwd)/setup.py install
