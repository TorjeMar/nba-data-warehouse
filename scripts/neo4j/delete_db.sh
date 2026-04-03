#!/bin/bash
set -e
source .env

docker exec ikt453_neo4j cypher-shell \
  -u "neo4j" \
  -p "$DB_PASSWORD" \
  -d "neo4j" \
  "MATCH (n) DETACH DELETE n;"