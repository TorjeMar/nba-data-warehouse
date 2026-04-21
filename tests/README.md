# Tests

This directory contains unit tests for the shared ETL layer and optional
integration tests for live database loaders.

## Run Unit Tests

```bash
uv run pytest tests/unit
```

## Run All Non-External Tests

```bash
uv run pytest
```

The MySQL integration tests are skipped by default.

## Run MySQL Integration Tests

Start the database stack and provide the same environment variables used by the
application:

```bash
docker compose up -d mysql
set -a
source .env
set +a
TEST_MYSQL_E2E=1 uv run pytest tests/integration/test_mysql_load.py
```

You can also use the helper script:

```bash
bash scripts/run_mysql_integration_tests.sh
```
