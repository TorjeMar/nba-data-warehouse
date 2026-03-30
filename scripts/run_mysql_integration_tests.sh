#!/usr/bin/env bash
set -e

echo "Loading env from .env ..."
set -a
source .env
set +a

echo "Resetting containers and volumes..."
docker compose down -v

echo "Starting containers..."
docker compose up -d

echo "Waiting for MySQL to become ready..."
until docker compose exec -T mysql mysqladmin ping -h 127.0.0.1 -uroot -p"${DB_PASSWORD}" --silent 2>/dev/null; do
  sleep 2
done

echo "Running MySQL integration tests..."
TEST_MYSQL_E2E=1 pytest tests/integration/test_mysql_load.py