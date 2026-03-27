# Data Loading And Transformation

Explain extraction, cleaning, transformation, and loading.

## Notes Seeded From Current Work

- A shared ETL layer is implemented in `src/etl/`.
- The ETL first flattens each game payload into player-level rows.
- It normalizes strings, converts empty values to null-like forms where appropriate, and converts minutes from `MM:SS` into seconds.
- It builds a shared `WarehouseRecord` model used by all backend loaders.
- Separate loaders exist for:
  - MySQL
  - MongoDB
  - Neo4j

Current gap:
- no upstream enrichment step yet for game date, season, matchup, or home/away metadata
