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

wait_for_mysql() {
  echo "[streaming] Waiting for MySQL..."
  until docker compose exec -T mysql \
    mysqladmin ping -h 127.0.0.1 -uroot -p"${DB_PASSWORD}" --silent >/dev/null 2>&1; do
    sleep 2
  done
  echo "[streaming] MySQL is ready."
}

wait_for_mongodb() {
  echo "[streaming] Waiting for MongoDB..."
  until docker compose exec -T mongodb mongosh \
    -u "${DB_USERNAME}" \
    -p "${DB_PASSWORD}" \
    --authenticationDatabase admin \
    --quiet "${DB_NAME}" \
    --eval "db.runCommand({ ping: 1 }).ok" >/dev/null 2>&1; do
    sleep 2
  done
  echo "[streaming] MongoDB is ready."
}

wait_for_neo4j() {
  echo "[streaming] Waiting for Neo4j..."
  until docker compose exec -T neo4j cypher-shell \
    -u neo4j \
    -p "${DB_PASSWORD}" \
    "RETURN 1;" >/dev/null 2>&1; do
    sleep 2
  done
  echo "[streaming] Neo4j is ready."
}

wait_for_kafka() {
  echo "[streaming] Waiting for Kafka broker..."
  until docker compose exec -T broker cub kafka-ready -b broker:9092 1 30 >/dev/null 2>&1; do
    sleep 2
  done
  echo "[streaming] Kafka broker is ready."
}

wait_for_services() {
  load_env
  wait_for_kafka
  wait_for_mysql
  wait_for_mongodb
  wait_for_neo4j
}

show_usage() {
  cat <<'EOF'
Usage:
  scripts/run_streaming.sh produce [producer args...]
  scripts/run_streaming.sh consume [consumer args...]
  scripts/run_streaming.sh demo [producer args...]
  scripts/run_streaming.sh fanout [--limit N] [producer args...]
  scripts/run_streaming.sh nightly [nightly args...]

Examples:
  scripts/run_streaming.sh produce --limit 100
  scripts/run_streaming.sh consume --backend mysql --limit 100
  scripts/run_streaming.sh demo --limit 100
  scripts/run_streaming.sh fanout --limit 100 --input data/box_scores.jsonl
  scripts/run_streaming.sh nightly --source-backend mysql --start-year 2024 --end-year 2026
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
  wait_for_services
  run_producer "$@"
}

run_fanout() {
  load_env
  docker compose up -d zookeeper broker mysql mongodb neo4j
  wait_for_services

  local limit="100"
  local producer_args=()
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --limit)
        if [[ $# -lt 2 ]]; then
          echo "Missing value for --limit"
          exit 1
        fi
        limit="$2"
        producer_args+=("$1" "$2")
        shift 2
        ;;
      *)
        producer_args+=("$1")
        shift
        ;;
    esac
  done

  uv run python -m src.etl.stream_consumer --backend mysql --group-id stream-mysql --limit "$limit" &
  local mysql_pid=$!
  uv run python -m src.etl.stream_consumer --backend mongodb --group-id stream-mongodb --limit "$limit" &
  local mongodb_pid=$!
  uv run python -m src.etl.stream_consumer --backend neo4j --group-id stream-neo4j --limit "$limit" &
  local neo4j_pid=$!

  trap 'kill "${mysql_pid-}" "${mongodb_pid-}" "${neo4j_pid-}" >/dev/null 2>&1 || true' EXIT

  run_producer "${producer_args[@]}"

  wait "$mysql_pid"
  wait "$mongodb_pid"
  wait "$neo4j_pid"
  trap - EXIT
}

run_nightly() {
  load_env
  docker compose up -d zookeeper broker mysql mongodb neo4j
  wait_for_services

  local source_backend="mysql"
  local topic="player-game-records"
  local broker="localhost:29092"
  local idle_polls_before_exit="10"
  local poll_timeout_ms="1000"
  local nightly_args=()

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --source-backend)
        source_backend="$2"
        nightly_args+=("$1" "$2")
        shift 2
        ;;
      --topic)
        topic="$2"
        nightly_args+=("$1" "$2")
        shift 2
        ;;
      --broker)
        broker="$2"
        nightly_args+=("$1" "$2")
        shift 2
        ;;
      --idle-polls-before-exit)
        idle_polls_before_exit="$2"
        shift 2
        ;;
      --poll-timeout-ms)
        poll_timeout_ms="$2"
        shift 2
        ;;
      *)
        nightly_args+=("$1")
        shift
        ;;
    esac
  done

  uv run python -m src.etl.stream_consumer \
    --backend mysql \
    --group-id nightly-mysql \
    --topic "$topic" \
    --broker "$broker" \
    --poll-timeout-ms "$poll_timeout_ms" \
    --idle-polls-before-exit "$idle_polls_before_exit" &
  local mysql_pid=$!

  uv run python -m src.etl.stream_consumer \
    --backend mongodb \
    --group-id nightly-mongodb \
    --topic "$topic" \
    --broker "$broker" \
    --poll-timeout-ms "$poll_timeout_ms" \
    --idle-polls-before-exit "$idle_polls_before_exit" &
  local mongodb_pid=$!

  uv run python -m src.etl.stream_consumer \
    --backend neo4j \
    --group-id nightly-neo4j \
    --topic "$topic" \
    --broker "$broker" \
    --poll-timeout-ms "$poll_timeout_ms" \
    --idle-polls-before-exit "$idle_polls_before_exit" &
  local neo4j_pid=$!

  trap 'kill "${mysql_pid-}" "${mongodb_pid-}" "${neo4j_pid-}" >/dev/null 2>&1 || true' EXIT

  uv run python -m src.pipelines.stream_new_games \
    --source-backend "$source_backend" \
    --topic "$topic" \
    --broker "$broker" \
    "${nightly_args[@]}"

  wait "$mysql_pid"
  wait "$mongodb_pid"
  wait "$neo4j_pid"
  trap - EXIT
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
  fanout)
    run_fanout "$@"
    ;;
  nightly)
    run_nightly "$@"
    ;;
  *)
    show_usage
    exit 1
    ;;
esac
