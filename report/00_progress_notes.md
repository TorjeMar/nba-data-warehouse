# Progress Notes

This file records work already completed in the repository that should be reflected in the final report.

## Completed So Far

- Dockerized infrastructure for MySQL, MongoDB, and Neo4j in `docker-compose.yml`
- Admin interfaces available for MySQL, MongoDB, and Neo4j
- Root README updated to describe the actual implementation and usage flow
- Project documentation scaffold added under `docs/`
- MySQL star schema created under `sql/mysql/001_star_schema.sql`
- MySQL pre-aggregated summary table definitions created under `sql/mysql/002_summary_tables.sql`
- MongoDB warehouse design created under `sql/mongodb/`
- Neo4j warehouse design created under `sql/neo4j/`
- Shared Python ETL transformation layer implemented under `src/etl/`
- Backend loaders implemented for MySQL, MongoDB, and Neo4j
- Dataset shape analyzed and documented as column-oriented game payloads rather than row-oriented JSONL

## Still Pending

- live validation of all loaders against running containers
- batch job execution logic
- streaming/Kafka functionality
- frontend design and implementation
- user roles and workflow descriptions
- formal comparison of relational vs NoSQL approaches
- final report prose and diagrams
