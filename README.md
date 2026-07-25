# NBA Data Warehouse

A data engineering project implementing an ETL pipeline for loading NBA box score data into relational, document, and graph databases. The project supports MySQL, MongoDB, Neo4j, and Kafka-based streaming through a shared Python ETL pipeline.

# Authors

Developed as a university group project by:

- Torje Martinsen
- Abraham Korh
- Jørgen Haugan Strand

---

## Tech Stack

- Python
- MySQL
- MongoDB
- Neo4j
- Kafka
- Docker

## Features

- Shared Python ETL pipeline for multiple database backends
- Relational data warehouse implemented in MySQL
- Document-oriented warehouse implemented in MongoDB
- Graph database implementation using Neo4j
- Kafka-based streaming pipeline for scalable data ingestion
- Dockerized development environment
- Automated tests for ETL components

## Dataset

The primary dataset is located at:

```
data/box_scores.jsonl
```

The dataset stores NBA box score information in a game-oriented JSONL format. During the ETL process, each game is transformed into individual player-level statistics before loading into the selected backend.

Reference example:

```
data.example/entry.json
```

---

# Project Structure

```
.
├── docker-compose.yml
├── sql
│   ├── mysql
│   ├── mongodb
│   └── neo4j
├── src
│   ├── clients
│   ├── etl
│   └── pipelines
├── scripts
├── tests
└── data
```

Main folders:

- **sql/mysql/** – MySQL warehouse schema
- **sql/mongodb/** – MongoDB collections, indexes and aggregations
- **sql/neo4j/** – Neo4j graph model and analytical queries
- **src/etl/** – Shared extraction and transformation logic
- **src/pipelines/** – CLI entry points
- **tests/** – Unit and integration tests

---

# Infrastructure

Start all services:

```bash
docker compose up -d
```

Service endpoints:

| Service | Address |
|---------|----------|
| MySQL Admin | http://localhost:8080 |
| MongoDB Admin | http://localhost:8081 |
| Neo4j Browser | http://localhost:7474 |

Default ports:

| Database | Port |
|----------|------|
| MySQL | 3306 |
| MongoDB | 27017 |
| Neo4j Bolt | 7687 |

Environment variables:

```
DB_USERNAME
DB_PASSWORD
```

stored in:

```
.env
```

---

# Python Setup

Install dependencies:

```bash
uv sync
```

Run tests:

```bash
uv run pytest
```

MySQL integration tests require:

```bash
TEST_MYSQL_E2E=1
```

---

# Data Warehouse Designs

## MySQL

Implements a traditional star schema.

Main tables:

- dim_team
- dim_player
- dim_position
- dim_game
- dim_date
- fact_player_game_stats

Schema:

```
sql/mysql/
```

---

## MongoDB

Implements a document-oriented warehouse.

Primary collection:

```
player_game_stats
```

Contains:

- indexes
- aggregation pipelines
- validation rules

---

## Neo4j

Implements a graph-based warehouse.

Core relationship:

```
(Player)-[:PLAYED_IN]->(Game)
```

Includes:

- constraints
- graph model
- analytical Cypher queries

---

# ETL Pipeline

Dry-run:

```bash
python -m src.pipelines.load_box_scores \
    --backend mysql \
    --dry-run \
    --limit 100
```

Load MySQL:

```bash
python -m src.pipelines.load_box_scores --backend mysql
```

Load MongoDB:

```bash
python -m src.pipelines.load_box_scores --backend mongodb
```

Load Neo4j:

```bash
python -m src.pipelines.load_box_scores --backend neo4j
```

Load every backend:

```bash
python -m src.pipelines.load_box_scores --backend all
```

Useful options:

```
--input
--batch-size
--limit
```

---

# Streaming Architecture

Streaming is implemented using Apache Kafka.

Components:

- Kafka Broker
- ZooKeeper
- MySQL
- MongoDB
- Neo4j

Start services:

```bash
docker compose up -d \
    zookeeper \
    broker \
    mysql \
    mongodb \
    neo4j
```

Run streaming pipeline:

```bash
scripts/run_streaming.sh fanout \
    --limit 100 \
    --input data/box_scores.jsonl
```

The producer publishes NBA player statistics to Kafka while independent consumer groups load data into each warehouse backend.

---

# Getting Started

1. Clone the repository.
2. Start the Docker services.
3. Install Python dependencies.
4. Apply the database schema for the selected backend.
5. Run the ETL pipeline.

---

# License

This repository is provided for educational and portfolio purposes.
