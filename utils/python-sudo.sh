#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
VENV_PYTHON="$(dirname $DIR)/venv/bin/python"
sudo "${VENV_PYTHON}" "$@"