#!/bin/bash
set -e
source .env

: "${DB_NAME:?DB_NAME is not set}"

docker exec -i ikt453_mysql mysql \
  -u"$DB_USERNAME" \
  -p"$DB_PASSWORD" \
  -e "CREATE DATABASE IF NOT EXISTS \`$DB_NAME\`;"

docker exec -i ikt453_mysql mysql \
  -u"$DB_USERNAME" \
  -p"$DB_PASSWORD" \
  "$DB_NAME" \
  < ./sql/mysql/001_star_schema.sql

docker exec -i ikt453_mysql mysql \
  -u"$DB_USERNAME" \
  -p"$DB_PASSWORD" \
  "$DB_NAME" \
  < ./sql/mysql/002_summary_tables.sql
  