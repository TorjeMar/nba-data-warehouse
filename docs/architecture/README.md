# Architecture Notes

## System Overview

The project implements the same basketball analytics warehouse across three storage models:
- MySQL for a relational star schema
- MongoDB for a document-oriented analytical store
- Neo4j for a graph-oriented analytical model

All three backends are fed from the same ETL transformation layer in `src/etl/`.

## Business Grain

The shared analytical grain is:
- one player stat line for one game and one team

This grain is preserved across all backends so that cross-backend comparisons stay meaningful.

## Source Shape

The main source file `data/box_scores.jsonl` is column-oriented by game.

That means each line contains:
- one game payload
- multiple player entries indexed by string row ids
- repeated game and team attributes across the same payload

The ETL layer normalizes that into one canonical warehouse record per player appearance.

## Backend Mapping

### MySQL

Relational warehouse pattern:
- dimensions for team, player, game, date, and position
- one fact table for player game stats
- separate summary tables for common aggregate workloads

Main files:
- [001_star_schema.sql](/home/abraham/uni/ikt453/project/v1/sql/mysql/001_star_schema.sql#L1)
- [002_summary_tables.sql](/home/abraham/uni/ikt453/project/v1/sql/mysql/002_summary_tables.sql#L1)

### MongoDB

Document warehouse pattern:
- one fact-like collection named `player_game_stats`
- embedded `team`, `player`, and `stats` subdocuments
- optional supporting collections for master/reference data
- aggregation pipelines for materialized summaries

Main files:
- [001_document_model.js](/home/abraham/uni/ikt453/project/v1/sql/mongodb/001_document_model.js#L1)
- [002_indexes.js](/home/abraham/uni/ikt453/project/v1/sql/mongodb/002_indexes.js#L1)
- [003_aggregations.js](/home/abraham/uni/ikt453/project/v1/sql/mongodb/003_aggregations.js#L1)

### Neo4j

Graph warehouse pattern:
- nodes for `Player`, `Team`, `Game`, `Date`, and `Position`
- box score measures stored on the `PLAYED_IN` relationship
- graph constraints for source identifiers
- Cypher queries for analytical rollups

Main files:
- [001_constraints.cypher](/home/abraham/uni/ikt453/project/v1/sql/neo4j/001_constraints.cypher#L1)
- [002_graph_model.cypher](/home/abraham/uni/ikt453/project/v1/sql/neo4j/002_graph_model.cypher#L1)
- [003_analytics.cypher](/home/abraham/uni/ikt453/project/v1/sql/neo4j/003_analytics.cypher#L1)
- [004_load_shape.cypher](/home/abraham/uni/ikt453/project/v1/sql/neo4j/004_load_shape.cypher#L1)

## ETL Flow

The ETL process has four stages:

1. Read each game payload from `data/box_scores.jsonl`.
2. Flatten the column-oriented payload into player-level rows.
3. Transform each row into a shared `WarehouseRecord`.
4. Load that record into MySQL, MongoDB, or Neo4j.

Main files:
- [transform.py](/home/abraham/uni/ikt453/project/v1/src/etl/transform.py#L1)
- [models.py](/home/abraham/uni/ikt453/project/v1/src/etl/models.py#L1)
- [load_box_scores.py](/home/abraham/uni/ikt453/project/v1/src/pipelines/load_box_scores.py#L1)

## Current Gaps

These are still open by design:
- enrichment for game date and season metadata
- automated schema/bootstrap execution before ETL
- analytical frontend
- scheduled batch orchestration
