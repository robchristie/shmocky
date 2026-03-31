#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

: "${SHMOCKY_API_HOST:=127.0.0.1}"
: "${SHMOCKY_API_PORT:=8011}"

export SHMOCKY_API_HOST
export SHMOCKY_API_PORT

uv sync --extra dev
uv run shmocky-api
