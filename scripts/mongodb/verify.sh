#!/bin/bash
set -euo pipefail

source .env

VERIFY_JS=$(cat <<'EOF'
try {
  const expectedCollections = [
    "player_game_stats",
    "teams",
    "players",
    "games",
    "calendar",
  ];

  function fail(message) {
    throw new Error(message);
  }

  function assert(condition, message) {
    if (!condition) {
      fail(message);
    }
  }

  function stringify(value) {
    return JSON.stringify(value);
  }

  function sameKey(actual, expected) {
    return stringify(actual) === stringify(expected);
  }

  function getIndex(collectionName, indexName) {
    return db.getCollection(collectionName).getIndexes().find((idx) => idx.name === indexName);
  }

  function assertIndex(collectionName, indexName, expectedKey, expectedUnique) {
    const index = getIndex(collectionName, indexName);
    assert(!!index, `Missing index ${collectionName}.${indexName}`);

    assert(
      sameKey(index.key, expectedKey),
      `Index ${collectionName}.${indexName} has unexpected key: ${stringify(index.key)}`,
    );

    if (expectedUnique) {
      assert(index.unique === true, `Index ${collectionName}.${indexName} must be unique`);
    } else {
      assert(index.unique !== true, `Index ${collectionName}.${indexName} must not be unique`);
    }
  }

  const collections = db.getCollectionNames();
  for (const name of expectedCollections) {
    assert(collections.includes(name), `Missing collection: ${name}`);
  }

  const info = db.getCollectionInfos({ name: "player_game_stats" })[0];
  assert(!!info, "Collection info missing for player_game_stats");
  assert(
    !!info.options?.validator?.$jsonSchema,
    "Validator missing on player_game_stats (expected $jsonSchema validator)",
  );

  assertIndex(
    "player_game_stats",
    "uq_game_team_player",
    { sourceGameId: 1, "team.sourceTeamId": 1, "player.sourcePersonId": 1 },
    true,
  );
  assertIndex("player_game_stats", "idx_game_date", { gameDate: 1 }, false);
  assertIndex("player_game_stats", "idx_team_date", { "team.sourceTeamId": 1, gameDate: 1 }, false);
  assertIndex(
    "player_game_stats",
    "idx_player_date",
    { "player.sourcePersonId": 1, gameDate: 1 },
    false,
  );
  assertIndex(
    "player_game_stats",
    "idx_season_player_team",
    { seasonLabel: 1, "player.sourcePersonId": 1, "team.sourceTeamId": 1 },
    false,
  );

  assertIndex("teams", "uq_team_source_id", { sourceTeamId: 1 }, true);
  assertIndex("players", "uq_player_source_id", { sourcePersonId: 1 }, true);
  assertIndex("games", "uq_game_source_id", { sourceGameId: 1 }, true);
  assertIndex("calendar", "uq_calendar_date_key", { dateKey: 1 }, true);

  print("MongoDB bootstrap verification passed.");
  quit(0);
} catch (err) {
  print(`MongoDB bootstrap verification failed: ${err.message}`);
  quit(1);
}
EOF
)

docker exec -i ikt453_mongodb mongosh \
  -u "$DB_USERNAME" \
  -p "$DB_PASSWORD" \
  --authenticationDatabase admin \
  --quiet "$DB_NAME" --eval "$VERIFY_JS"