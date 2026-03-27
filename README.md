# IKT453 Data Warehousing Project

This repository contains a basketball box score data warehousing project with three backend targets:
- MySQL for the relational star schema warehouse
- MongoDB for the document-oriented alternative
- Neo4j for the graph-oriented alternative

The current implementation includes:
- Dockerized database infrastructure
- MySQL star schema and summary-table DDL
- MongoDB document model, indexes, and aggregation examples
- Neo4j constraints, graph model, load shape, and analytical queries
- a shared Python ETL pipeline that transforms the source dataset for all three backends

## Dataset

The main source file is `data/box_scores.jsonl`.

Important detail:
- this is not row-oriented JSONL
- each line is a game-level, column-oriented payload
- the ETL layer flattens each game payload into one player stat line per row

Reference files:
- [notes/data.md](/home/abraham/uni/ikt453/project/v1/notes/data.md#L1)
- [data.example/entry.json](/home/abraham/uni/ikt453/project/v1/data.example/entry.json#L1)

## Project Structure

- `docker-compose.yml`: local database stack
- `sql/mysql/`: MySQL warehouse schema and summary tables
- `sql/mongodb/`: MongoDB collection model, indexes, and aggregations
- `sql/neo4j/`: Neo4j constraints, model, analytics, and load pattern
- `src/clients/`: Python connection helpers
- `src/etl/`: shared extraction and transformation code
- `src/pipelines/`: CLI entry points for loading data
- `docs/`: architecture and implementation notes
- `scripts/`: helper scripts for dataset acquisition

## Infrastructure

Start the database services with:

```bash
docker compose up -d
```

Access points:
- MySQL admin: `http://localhost:8080`
- MongoDB admin: `http://localhost:8081`
- Neo4j browser: `http://localhost:7474`

Default service ports:
- MySQL: `3306`
- MongoDB: `27017`
- Neo4j Bolt: `7687`

The compose stack expects `DB_USERNAME` and `DB_PASSWORD` in `.env`.

## Python Setup

Install dependencies:

```bash
uv sync
```

Current SDK dependencies:
- `mysql-connector-python`
- `pymongo`
- `neo4j`

## Warehouse Designs

### MySQL

Main schema files:
- [001_star_schema.sql](/home/abraham/uni/ikt453/project/v1/sql/mysql/001_star_schema.sql#L1)
- [002_summary_tables.sql](/home/abraham/uni/ikt453/project/v1/sql/mysql/002_summary_tables.sql#L1)

Design grain:
- one player stat line for one game and one team

Core tables:
- `dim_team`
- `dim_player`
- `dim_position`
- `dim_game`
- `dim_date`
- `fact_player_game_stats`

### MongoDB

Main design files:
- [001_document_model.js](/home/abraham/uni/ikt453/project/v1/sql/mongodb/001_document_model.js#L1)
- [002_indexes.js](/home/abraham/uni/ikt453/project/v1/sql/mongodb/002_indexes.js#L1)
- [003_aggregations.js](/home/abraham/uni/ikt453/project/v1/sql/mongodb/003_aggregations.js#L1)

Design grain:
- one document per player stat line for one game and one team

Primary collection:
- `player_game_stats`

### Neo4j

Main design files:
- [001_constraints.cypher](/home/abraham/uni/ikt453/project/v1/sql/neo4j/001_constraints.cypher#L1)
- [002_graph_model.cypher](/home/abraham/uni/ikt453/project/v1/sql/neo4j/002_graph_model.cypher#L1)
- [003_analytics.cypher](/home/abraham/uni/ikt453/project/v1/sql/neo4j/003_analytics.cypher#L1)
- [004_load_shape.cypher](/home/abraham/uni/ikt453/project/v1/sql/neo4j/004_load_shape.cypher#L1)

Design grain:
- one `PLAYED_IN` relationship per player, game, and team

## ETL

Main pipeline:
- [load_box_scores.py](/home/abraham/uni/ikt453/project/v1/src/pipelines/load_box_scores.py#L1)

Dry-run the transform layer without touching any database:

```bash
python -m src.pipelines.load_box_scores --backend mysql --dry-run --limit 100
```

Load a backend:

```bash
python -m src.pipelines.load_box_scores --backend mysql
python -m src.pipelines.load_box_scores --backend mongodb
python -m src.pipelines.load_box_scores --backend neo4j
```

Load all backends:

```bash
python -m src.pipelines.load_box_scores --backend all
```

Optional flags:
- `--input data/box_scores.jsonl`
- `--batch-size 1000`
- `--limit 500`

Important assumptions:
- game date and season metadata are not present in the current source file, so those warehouse fields remain nullable until enriched upstream
- MySQL loading assumes the schema SQL has already been applied
- Neo4j loading assumes constraints and base model scripts have already been applied
- MongoDB loading assumes the target database exists and the validator/index scripts are applied or will be applied separately

## Suggested Execution Order

1. Start the database containers.
2. Apply the schema/model files for the backend you want to test.
3. Install Python dependencies.
4. Run the ETL pipeline with `--dry-run`.
5. Run the ETL pipeline against the selected backend.

## Documentation

Documentation index:
- [docs/README.md](/home/abraham/uni/ikt453/project/v1/docs/README.md#L1)
- [docs/architecture/README.md](/home/abraham/uni/ikt453/project/v1/docs/architecture/README.md#L1)
- [src/etl/README.md](/home/abraham/uni/ikt453/project/v1/src/etl/README.md#L1)

## Course Notes

The original course brief is still part of the repository history and project context, but the root README is now focused on the actual implementation in this repository.
