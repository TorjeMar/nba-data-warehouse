# Summary Tables And Batch Jobs

Describe pre-aggregated summaries and batch processing.

## Notes Seeded From Current Work

- Summary-table DDL exists in `sql/mysql/002_summary_tables.sql`.
- Current summary tables:
  - `agg_team_game_totals`
  - `agg_player_season_totals`
- MongoDB also has aggregation examples for materialized summaries.

Current gap:
- no automated batch execution layer yet
- no MySQL population SQL scripts yet
