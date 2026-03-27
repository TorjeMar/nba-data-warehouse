# Relational Warehouse

Describe the MySQL warehouse design.

## Notes Seeded From Current Work

- The MySQL design is a star schema.
- Fact grain: one player stat line for one game and one team.
- Dimension tables:
  - `dim_team`
  - `dim_player`
  - `dim_position`
  - `dim_game`
  - `dim_date`
- Fact table:
  - `fact_player_game_stats`

Implementation references:
- `sql/mysql/001_star_schema.sql`
