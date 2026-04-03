#!/bin/bash
set -e
source .env

docker exec -i ikt453_neo4j cypher-shell \
  -u neo4j \
  -p "$DB_PASSWORD" \
  -d neo4j < ./sql/neo4j/001_constraints.cypher

docker exec -i ikt453_neo4j cypher-shell \
  -u neo4j \
  -p "$DB_PASSWORD" \
  -d neo4j < ./sql/neo4j/002_graph_model.cypher