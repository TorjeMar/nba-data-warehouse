#!/usr/bin/env bash
set -euo pipefail

echo "Loading env from .env ..."
set -a
source .env
set +a

echo "Refreshing MySQL summary tables ..."
python -m src.pipelines.refresh_mysql_summaries --validate
