#!/bin/sh
set -eu

echo "Waiting for ksqlDB to be ready..."

until curl -sf http://ksqldb-server:8088/info >/dev/null; do
  sleep 2
done

until curl -sf -X POST http://ksqldb-server:8088/ksql \
  -H "Content-Type: application/vnd.ksql.v1+json; charset=utf-8" \
  -d '{"ksql":"SHOW PROPERTIES;","streamsProperties":{}}' >/dev/null; do
  echo "ksqlDB not ready for statements yet, waiting..."
  sleep 2
done

echo "ksqlDB is ready. Applying SQL..."

SQL_ESCAPED=$(awk '
  BEGIN { printf "" }
  {
    gsub(/\\/,"\\\\");
    gsub(/"/,"\\\"");
    printf "%s\\n", $0
  }
' /init/001_live_dashboard.sql)

curl -sS -X POST http://ksqldb-server:8088/ksql \
  -H "Content-Type: application/vnd.ksql.v1+json; charset=utf-8" \
  -d "{\"ksql\":\"${SQL_ESCAPED}\",\"streamsProperties\":{}}"

echo
echo "ksqlDB initialization complete."