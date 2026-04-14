## Environment Variables
```bash
DB_NAME=...
DB_PASSWORD=...
DB_USERNAME=...
PATH_TO_DATA=...
PATH_TO_SEASON_DATA=...
```

## How to run
```bash
docker compose up -d 
export DATA=path/to/data
uv run -m src.pipelines.load_box_scores --backend all --input $DATA --limit 500     
uv run -m src.frontend.app   
```

