# ETL Notes

The current source file `data/box_scores.jsonl` is column-oriented by game, not row-oriented by player.

The ETL layer handles that in two stages:
- flatten each game payload into one row per player entry
- transform each row into a shared warehouse record used by all three backends

Main files:
- [transform.py](transform.py#L1)
- [models.py](models.py#L1)
- [load_mysql.py](load_mysql.py#L1)
- [load_mongodb.py](load_mongodb.py#L1)
- [load_neo4j.py](load_neo4j.py#L1)

Entry point:
- `python -m src.pipelines.load_box_scores --backend mysql --limit 100`

Dry run:
- `python -m src.pipelines.load_box_scores --backend mysql --dry-run --limit 100`

Backend loads:
- `python -m src.pipelines.load_box_scores --backend mysql`
- `python -m src.pipelines.load_box_scores --backend mongodb`
- `python -m src.pipelines.load_box_scores --backend neo4j`

Data Enrichment:

When fields are missing from box score payloads (for example game date, matchup, and home/away context), the ETL loads supplemental game metadata from nba_api season files during `load_box_scores`.
If a season/season_type file does not exist and the API returns no rows, the pipeline writes an explicit empty JSON file ([]) so future runs skip repeated fetch attempts.
After season metadata is available, the transform step enriches each player-game record with:
- game_date
- season_label
- matchup_label
- home_away (team-perspective, derived from matchup metadata)

Notes:
- the transformation layer does not require live database connections for `--dry-run`
- game date and season attributes are modeled but currently not present in the source payload
