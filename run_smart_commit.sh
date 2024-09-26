#!/bin/bash
exec < /dev/tty  # Allow interactive shell commands
poetry run python clabs_smart_commit.py "$@"