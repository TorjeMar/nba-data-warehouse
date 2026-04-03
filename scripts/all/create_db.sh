#!/bin/bash

source .env
./scripts/mongodb/create_db.sh
echo "Created MongoDB database: $DB_NAME"
./scripts/mysql/create_db.sh
echo "Created MySQL database: $DB_NAME"
./scripts/neo4j/create_db.sh
echo "Created Neo4j database: neo4j"
