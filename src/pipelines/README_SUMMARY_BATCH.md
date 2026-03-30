
## What it does

It refreshes these pre-aggregated tables from the **star schema**:

- `agg_team_game_totals`
- `agg_player_season_totals`

## Why this approach

This implementation uses a **full refresh** strategy:

1. delete existing rows from the summary tables
2. rebuild them from `fact_player_game_stats` + dimensions
3. commit as one transaction

## Files


```text
<project-root>/
  sql/
    mysql/
      003_populate_agg_team_game_totals.sql
      004_populate_agg_player_season_totals.sql
  src/
    pipelines/
      refresh_mysql_summaries.py
  scripts/
    run_mysql_summary_batch.sh
```

## Run order

1. Load the star schema first:

```bash
python -m src.pipelines.load_box_scores --backend mysql
```

2. Then refresh the summary tables:

```bash
python -m src.pipelines.refresh_mysql_summaries --validate
```

or

```bash
bash scripts/run_mysql_summary_batch.sh
```

## What each summary table contains

### agg_team_game_totals
One row per **team per game**, aggregated from all player rows for that team in that game.

### agg_player_season_totals
One row per **player per season per team**, aggregated from all fact rows for that player's games in that season.

## Manual verification

```sql
SELECT COUNT(*) FROM agg_team_game_totals;
SELECT COUNT(*) FROM agg_player_season_totals;

SELECT * FROM agg_team_game_totals LIMIT 5;
SELECT * FROM agg_player_season_totals LIMIT 5;
```
