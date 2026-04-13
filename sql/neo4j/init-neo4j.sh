#!/bin/bash
# Wrapper entrypoint: starts Neo4j, waits for readiness, runs .cypher init scripts.

/startup/docker-entrypoint.sh neo4j &
NEO4J_PID=$!

echo "Waiting for Neo4j to become ready..."
until cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "RETURN 1" &>/dev/null; do
  sleep 2
done
echo "Neo4j is ready."

for f in /docker-entrypoint-initdb.d/*.cypher; do
  echo "Running $f ..."
  cypher-shell -u neo4j -p "$NEO4J_PASSWORD" < "$f"
done

wait $NEO4J_PID
