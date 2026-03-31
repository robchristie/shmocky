#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${REPO_ROOT}"

: "${SHMOCKY_FRONTEND_HOST:=0.0.0.0}"
: "${SHMOCKY_FRONTEND_PORT:=4321}"
: "${SHMOCKY_API_URL:=http://127.0.0.1:${SHMOCKY_API_PORT:-8011}}"
: "${SHMOCKY_ALLOWED_HOSTS:=*}"

export SHMOCKY_API_URL
export SHMOCKY_ALLOWED_HOSTS

npm --prefix apps/web run dev -- --host "${SHMOCKY_FRONTEND_HOST}" --port "${SHMOCKY_FRONTEND_PORT}"
