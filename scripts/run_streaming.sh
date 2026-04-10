#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

load_env() {
  if [[ -f .env ]]; then
    set -a
    source .env
    set +a
  fi
}

show_usage() {
  cat <<'EOF'
Usage:
  scripts/run_streaming.sh produce [producer args...]
  scripts/run_streaming.sh consume [consumer args...]
  scripts/run_streaming.sh demo [producer args...]

Examples:
  scripts/run_streaming.sh produce --limit 100
  scripts/run_streaming.sh consume --backend mysql --limit 100
  scripts/run_streaming.sh demo --limit 100
EOF
}

run_producer() {
  load_env
  uv run python -m src.etl.stream_producer "$@"
}

run_consumer() {
  load_env
  uv run python -m src.etl.stream_consumer "$@"
}

run_demo() {
  load_env
  docker compose up -d zookeeper broker mysql mongodb neo4j
  run_producer "$@"
}

if [[ $# -lt 1 ]]; then
  show_usage
  exit 1
fi

command="$1"
shift

case "$command" in
  produce)
    run_producer "$@"
    ;;
  consume)
    run_consumer "$@"
    ;;
  demo)
    run_demo "$@"
    ;;
  *)
    show_usage
    exit 1
    ;;
esac
