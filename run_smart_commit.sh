#!/bin/sh
exec < /dev/tty
poetry run python clabs_smart_commit.py "$@"
