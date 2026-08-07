#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

BRANCH="${DEPLOY_BRANCH:-active-dev}"

git fetch origin "$BRANCH"
git reset --hard "origin/$BRANCH"

docker compose up -d --build
docker image prune -f
