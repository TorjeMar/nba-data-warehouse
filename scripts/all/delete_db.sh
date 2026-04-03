#!/bin/bash

source .env
./scripts/mongodb/delete_db.sh
echo "Deleted MongoDB database: $DB_NAME"
./scripts/mysql/delete_db.sh
echo "Deleted MySQL database: $DB_NAME"
./scripts/neo4j/delete_db.sh
echo "Deleted all nodes in Neo4j database: neo4j"

