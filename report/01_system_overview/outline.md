# System Overview

Use this section for:
- application domain summary
- purpose of the warehouse
- high-level architecture
- user types and access patterns

## Notes Seeded From Current Work

- The project domain is basketball box score analytics.
- The repository currently targets three storage backends: MySQL, MongoDB, and Neo4j.
- The same transformed dataset is intended to feed all three backends through a shared ETL layer.
- The infrastructure is containerized with Docker Compose.
- An umbrella frontend is expected by the course requirements, but it has not been implemented yet.
