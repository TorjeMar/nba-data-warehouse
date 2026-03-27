# Source Layout

Reserved application structure for the implementation phase.

- `clients/` database connection wrappers and shared client factories
- `etl/` extraction, transformation, and loading logic
- `pipelines/` orchestration entry points for batch jobs
- `warehouse/` warehouse-specific domain logic and SQL helpers
