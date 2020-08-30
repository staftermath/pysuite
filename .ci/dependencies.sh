#!/bin/bash

pip install -r $(pwd)/requirements.txt
pip install pandas==${pd_version}
pip freeze
