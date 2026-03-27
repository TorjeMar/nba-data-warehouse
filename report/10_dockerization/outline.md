# Dockerization

Describe the containerized system setup.

## Notes Seeded From Current Work

- Docker Compose defines:
  - MySQL
  - phpMyAdmin
  - MongoDB
  - mongo-express
  - Neo4j
- Persistent Docker volumes are configured for each database.
- Credentials are supplied through `.env`.

Implementation reference:
- `docker-compose.yml`
