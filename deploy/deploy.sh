#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Edit it with real OPENAI_API_KEY, EXA_API_KEY, FRONTEND_ORIGIN and PUBLIC_API_URL, then re-run this script."
  exit 1
fi

docker compose up -d --build
docker compose ps
