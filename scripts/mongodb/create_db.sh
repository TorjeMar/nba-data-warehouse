#!/bin/bash
set -e
source .env

docker exec -i ikt453_mongodb mongosh \
  -u "$DB_USERNAME" \
  -p "$DB_PASSWORD" \
  --authenticationDatabase admin \
  "$DB_NAME" < ./sql/mongodb/001_document_model.js

docker exec -i ikt453_mongodb mongosh \
  -u "$DB_USERNAME" \
  -p "$DB_PASSWORD" \
  --authenticationDatabase admin \
  "$DB_NAME" < ./sql/mongodb/002_indexes.js

  