#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

BRANCH="${DEPLOY_BRANCH:-active-dev}"
LOG_FILE="deploy/watch.log"

LOCAL=$(git rev-parse HEAD)
git fetch origin "$BRANCH" --quiet
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" != "$REMOTE" ]; then
  echo "$(date -Iseconds) new commit on $BRANCH ($LOCAL -> $REMOTE), redeploying" >> "$LOG_FILE"
  ./deploy/redeploy.sh >> "$LOG_FILE" 2>&1
fi
