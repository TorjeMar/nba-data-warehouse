# ETL Notes

The current source file `data/box_scores.jsonl` is column-oriented by game, not row-oriented by player.

The ETL layer handles that in two stages:
- flatten each game payload into one row per player entry
- transform each row into a shared warehouse record used by all three backends

Main files:
- [transform.py](/home/abraham/uni/ikt453/project/v1/src/etl/transform.py#L1)
- [models.py](/home/abraham/uni/ikt453/project/v1/src/etl/models.py#L1)
- [load_mysql.py](/home/abraham/uni/ikt453/project/v1/src/etl/load_mysql.py#L1)
- [load_mongodb.py](/home/abraham/uni/ikt453/project/v1/src/etl/load_mongodb.py#L1)
- [load_neo4j.py](/home/abraham/uni/ikt453/project/v1/src/etl/load_neo4j.py#L1)

Entry point:
- `python -m src.pipelines.load_box_scores --backend mysql --limit 100`

Dry run:
- `python -m src.pipelines.load_box_scores --backend mysql --dry-run --limit 100`

Backend loads:
- `python -m src.pipelines.load_box_scores --backend mysql`
- `python -m src.pipelines.load_box_scores --backend mongodb`
- `python -m src.pipelines.load_box_scores --backend neo4j`

Notes:
- the transformation layer does not require live database connections for `--dry-run`
- game date and season attributes are modeled but currently not present in the source payload
