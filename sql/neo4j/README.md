# Neo4j Warehouse Design

This graph model treats a player stat line as a relationship-centered fact.

Why this shape:
- `PLAYED_IN` naturally captures the event grain of a player appearing in a game
- graph traversal makes it straightforward to connect players, teams, games, and dates
- keeping measures on the relationship preserves the analytical meaning of the box score

Files:
- `001_constraints.cypher` creates uniqueness constraints and supporting indexes
- `002_graph_model.cypher` documents the conceptual graph and seeds positions
- `003_analytics.cypher` contains starter analytical Cypher queries
- `004_load_shape.cypher` shows the expected ETL merge pattern
