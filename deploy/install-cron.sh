#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CRON_LINE="*/5 * * * * $REPO_DIR/deploy/watch.sh"

( crontab -l 2>/dev/null | grep -vF "$REPO_DIR/deploy/watch.sh" ; echo "$CRON_LINE" ) | crontab -
crontab -l
