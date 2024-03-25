#!/bin/bash

if [ -n "$GITHUB_ACTIONS" ]; then
    sed -i 's|file:///app|file:///|' requirements.txt
fi

python -m pip install --upgrade pip
pip install -r requirements.txt
