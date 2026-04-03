#!/bin/bash
set -e

source .env
: "${DB_NAME:?DB_NAME is not set}"

docker exec ikt453_mongodb mongosh \
    -u "$DB_USERNAME" \
    -p "$DB_PASSWORD" \
    --authenticationDatabase admin \
    --eval "db.getSiblingDB(\"$DB_NAME\").dropDatabase()"