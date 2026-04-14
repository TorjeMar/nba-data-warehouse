# Streaming System Guide

Before starting the streaming pipeline, start the required services with Docker:

```bash
docker compose up -d
```

This project includes a Kafka-based streaming pipeline for loading player box score events into the three warehouse backends:

- MySQL
- MongoDB
- Neo4j

The general workflow is:

1. Start the Docker services
2. Start the consumers
3. Start the producer
4. Open the frontend UI

## 1. Start the consumers

Each database has its own consumer, and they should be started in separate terminal windows. The consumers can run in parallel.

### MySQL consumer

```bash
python -m src.etl.stream_consumer_mysql --group-id mysql-loader
```

### MongoDB consumer

```bash
python -m src.etl.stream_consumer_mongodb --group-id mongodb-loader
```

### Neo4j consumer

```bash
python -m src.etl.stream_consumer_neo4j --group-id neo4j-loader
```

## 2. Start the producer

The producer reads from `data/box_scores.jsonl` and publishes player-game events to Kafka.

### Stream the entire dataset

```bash
python -m src.etl.stream_producer --input data/box_scores.jsonl
```

### Start from a specific event number

Use `--start-event` to skip ahead in the stream.

```bash
python -m src.etl.stream_producer --input data/box_scores.jsonl --start-event 10000
```

### Limit the number of events produced

Use `--limit` to stop after a given number of events.

```bash
python -m src.etl.stream_producer --input data/box_scores.jsonl --limit 10000
```

### Stream a specific event interval

You can combine `--start-event` and `--limit` to stream a specific range.

Example: stream events 10000 to 19999.

```bash
python -m src.etl.stream_producer --input data/box_scores.jsonl --start-event 10000 --limit 10000
```

## 3. Start the frontend UI

Open another terminal window and run:

```bash
python -m src.frontend.app
```

The frontend will then be available locally in your browser.

## Typical workflow

A normal streaming session will usually look like this:

```bash
docker compose up -d
```

Then in separate terminals:

```bash
python -m src.etl.stream_consumer_mysql --group-id mysql-loader
python -m src.etl.stream_consumer_mongodb --group-id mongodb-loader
python -m src.etl.stream_consumer_neo4j --group-id neo4j-loader
python -m src.frontend.app
python -m src.etl.stream_producer --input data/box_scores.jsonl
```

## Notes

- The consumers are designed to keep running, so you do not need to restart them every time you want to produce a new event range.
- The producer can be rerun with different `--start-event` and `--limit` values to demonstrate streaming in chunks.
- This makes it possible to stream part of the dataset, inspect the UI, and then continue with the next interval.

## Stop the services

When you are done, shut everything down with:

```bash
docker compose down -v
```
