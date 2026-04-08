#!/bin/bash
set -euo pipefail

source .env

run_scalar_query() {
	local query="$1"
	docker exec -i ikt453_neo4j cypher-shell \
		-u neo4j \
		-p "$DB_PASSWORD" \
		-d neo4j \
		--format plain \
		"$query" | tail -n 1 | tr -d '\r' | xargs
}

assert_named_exists() {
	local kind="$1"
	local name="$2"
	local query="$3"
	local value
	value=$(run_scalar_query "$query")
	if [[ "$value" != "1" ]]; then
		echo "Neo4j bootstrap verification failed: missing ${kind} '${name}'"
		exit 1
	fi
}

assert_named_exists \
	"constraint" \
	"team_source_id_unique" \
	"SHOW CONSTRAINTS YIELD name WHERE name = 'team_source_id_unique' RETURN count(*) AS c;"
assert_named_exists \
	"constraint" \
	"player_source_id_unique" \
	"SHOW CONSTRAINTS YIELD name WHERE name = 'player_source_id_unique' RETURN count(*) AS c;"
assert_named_exists \
	"constraint" \
	"game_source_id_unique" \
	"SHOW CONSTRAINTS YIELD name WHERE name = 'game_source_id_unique' RETURN count(*) AS c;"
assert_named_exists \
	"constraint" \
	"date_key_unique" \
	"SHOW CONSTRAINTS YIELD name WHERE name = 'date_key_unique' RETURN count(*) AS c;"
assert_named_exists \
	"constraint" \
	"position_code_unique" \
	"SHOW CONSTRAINTS YIELD name WHERE name = 'position_code_unique' RETURN count(*) AS c;"

assert_named_exists \
	"index" \
	"game_season_label" \
	"SHOW INDEXES YIELD name WHERE name = 'game_season_label' RETURN count(*) AS c;"
assert_named_exists \
	"index" \
	"date_full_date" \
	"SHOW INDEXES YIELD name WHERE name = 'date_full_date' RETURN count(*) AS c;"

seed_count=$(run_scalar_query "MATCH (p:Position) WHERE p.positionCode IN ['', 'G', 'F', 'C', 'G-F', 'F-C'] RETURN count(DISTINCT p.positionCode) AS c;")
if [[ "$seed_count" != "6" ]]; then
	echo "Neo4j bootstrap verification failed: expected 6 seeded Position codes, found $seed_count"
	exit 1
fi

echo "Neo4j bootstrap verification passed."
