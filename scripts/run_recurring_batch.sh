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

usage() {
  cat <<'EOF'
Usage:
  scripts/run_recurring_batch.sh [--backend <mysql|mongodb|neo4j|all>] [--input <path>] [--skip-load] [--skip-summary]

Examples:
  scripts/run_recurring_batch.sh
  scripts/run_recurring_batch.sh --backend all --input data/box_scores.jsonl
  scripts/run_recurring_batch.sh --skip-load --skip-summary

Notes:
  - This is a scheduler-friendly entrypoint for recurring warehouse refresh.
  - It is rerun-safe with the current upsert/merge loading strategy.
EOF
}

BACKEND="all"
INPUT_PATH="data/box_scores.jsonl"
SKIP_LOAD=0
SKIP_SUMMARY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend)
      BACKEND="$2"
      shift 2
      ;;
    --input)
      INPUT_PATH="$2"
      shift 2
      ;;
    --skip-load)
      SKIP_LOAD=1
      shift
      ;;
    --skip-summary)
      SKIP_SUMMARY=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ "$BACKEND" != "mysql" && "$BACKEND" != "mongodb" && "$BACKEND" != "neo4j" && "$BACKEND" != "all" ]]; then
  echo "Invalid --backend value: $BACKEND"
  exit 1
fi

load_env

echo "[batch] Starting required services..."
docker compose up -d mysql mongodb neo4j

if [[ "$SKIP_LOAD" -eq 0 ]]; then
  echo "[batch] Running warehouse load (backend=$BACKEND, input=$INPUT_PATH)..."
  uv run python -m src.pipelines.load_box_scores --backend "$BACKEND" --input "$INPUT_PATH"
else
  echo "[batch] Skipping warehouse load (--skip-load)."
fi

if [[ "$SKIP_SUMMARY" -eq 0 ]]; then
  if [[ "$BACKEND" == "mysql" || "$BACKEND" == "all" ]]; then
    echo "[batch] Refreshing MySQL summaries..."
    uv run python -m src.pipelines.refresh_mysql_summaries --validate
  else
    echo "[batch] Skipping MySQL summaries because backend=$BACKEND."
  fi
else
  echo "[batch] Skipping summary refresh (--skip-summary)."
fi

echo "[batch] Recurring batch run completed successfully."
