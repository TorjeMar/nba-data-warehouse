# NoSQL Alternatives

Describe the MongoDB and Neo4j implementations and how relational warehouse ideas were mapped.

## Notes Seeded From Current Work

MongoDB:
- fact-like `player_game_stats` collection
- embedded `team`, `player`, and `stats` subdocuments
- validator and index design already written
- aggregation examples already written

Neo4j:
- `Player`, `Team`, `Game`, `Date`, and `Position` nodes
- `PLAYED_IN` relationship carries the box score measures
- constraints and query examples already written
- ETL load shape already written

Implementation references:
- `sql/mongodb/`
- `sql/neo4j/`
