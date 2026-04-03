#!/bin/bash
set -e

source .env

docker exec ikt453_mongodb mongosh \
  -u "$DB_USERNAME" \
  -p "$DB_PASSWORD" \
  --authenticationDatabase admin \
  "$DB_NAME" \
  --eval "db.getCollectionNames()"