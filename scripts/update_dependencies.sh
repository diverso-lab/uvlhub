#!/bin/bash

# Update pip
pip install --upgrade pip

# Upgrade all packages
pip freeze | cut -d = -f 1 | xargs -n1 pip install --upgrade

# Update requirements.txt
pip freeze > requirements.txt

echo "Update completed!"