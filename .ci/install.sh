#!/bin/bash

set -e

echo $(which python)
python $(pwd)/setup.py install
