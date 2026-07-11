#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$PROJECT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: Docker is not installed or is not in PATH." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: Docker Compose v2 is required (docker compose)." >&2
  exit 1
fi

ACTION=${1:-up}
PROFILE=${2:-company}

case "$ACTION" in
  deepseek|qwen|company)
    PROFILE=$ACTION
    ACTION=up
    ;;
esac

case "$PROFILE" in
  deepseek) PROFILE_FILE=.env.deepseek.example ;;
  qwen) PROFILE_FILE=.env.qwen.example ;;
  company) PROFILE_FILE=.env.example ;;
  *)
    echo "Error: model profile must be company, deepseek, or qwen." >&2
    exit 2
    ;;
esac

if [ ! -f .env ]; then
  cp "$PROFILE_FILE" .env
  echo "Created .env from $PROFILE_FILE."
  echo "Before a real demo, set Microsoft credentials and verify LLM_BASE_URL in .env."
fi

case "$ACTION" in
  up|detached|-d)
    if grep -q '^LLM_API_KEY=replace-with-' .env; then
      echo "Error: edit .env and replace LLM_API_KEY with your official API key." >&2
      exit 1
    fi
    ;;
esac

case "$ACTION" in
  up)
    exec docker compose up --build
    ;;
  detached|-d)
    docker compose up --build -d
    echo "FlowMate is running at http://localhost:${PORT:-8000}"
    echo "View logs with: ./start-linux.sh logs"
    ;;
  test)
    docker compose build
    exec docker compose run --rm flowmate python -m unittest discover -s tests -v
    ;;
  logs)
    exec docker compose logs -f flowmate
    ;;
  down|stop)
    exec docker compose down
    ;;
  *)
    echo "Usage: ./start-linux.sh [up|detached|test|logs|down] [company|deepseek|qwen]" >&2
    echo "       ./start-linux.sh [company|deepseek|qwen]" >&2
    exit 2
    ;;
esac
