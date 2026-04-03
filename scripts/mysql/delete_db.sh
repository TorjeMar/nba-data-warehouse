#!/bin/bash
set -e
source .env

: "${DB_NAME:?DB_NAME is not set}"

docker exec -i ikt453_mysql mysql \
  -u"$DB_USERNAME" \
  -p"$DB_PASSWORD" \
  -e "DROP DATABASE IF EXISTS \`$DB_NAME\`;"