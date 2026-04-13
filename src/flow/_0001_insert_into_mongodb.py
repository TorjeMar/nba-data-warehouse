import os
import re
import pandas as pd
from dotenv import load_dotenv
from src.crud import mongodb
from src.clients import connect_mongodb
from src.utils import disk, jhash, timestamp
from tqdm import tqdm

def normalize_matchup(record: dict) -> dict:
    matchup = record.get("MATCHUP", "")
    if 'vs.' in matchup:
        home_team, away_team = map(str.strip, matchup.split('vs.'))
    if '@' in matchup:
        away_team, home_team = map(str.strip, matchup.split('@'))
    
    record.pop("MATCHUP", None)
    record.pop("TEAM_ID", None)
    record.pop("TEAM_ABBREVIATION", None)

    return {
        **record,
        "HOME_TEAM": home_team,
        "AWAY_TEAM": away_team,
    }


load_dotenv()

path_game_dates = 'data/season'
path_box_scores = 'data/box_scores.jsonl'

if __name__ == "__main__":
    # TODO: Proper deduplication

    conn = connect_mongodb()

    # -----------------------
    # Insert game dates
    # -----------------------
    game_dates = disk.listdir(path_game_dates)
    game_dates = list(filter(lambda x: x.endswith('.json'), game_dates))

    seen = set()

    def dedup(seen: set, record: dict):
        h = record['jhash']
        if h in seen:
            return True
        
        seen.add(h)
        return True
    
    

    hash_and_stamp = lambda record: {
        **record, 
        'created_at': timestamp(),
        'updated_at': timestamp(),
        'jhash': jhash(record),
    }


    for path in tqdm(game_dates, total=len(game_dates)):
        content = disk.read_json(path)

        name = os.path.basename(path)
        name, _ = os.path.splitext(name)
        meta = re.match(r'games_(\d{4}-\d{2})_(\w+)', name)
        meta = dict(zip(['SEASON_LABEL', 'SEASON_TYPE'], meta.groups()))
        
        

        records = list(map(lambda x: hash_and_stamp({**normalize_matchup(x), **meta}), content))

        mongodb.insert(
            database=conn,
            filter_fn=lambda record: dedup(seen, record),
            collection_name='raw_game_dates',
            records=records
        )
    
    # -----------------------
    # Insert box scores
    # -----------------------
        box_scores = disk.read_jsonl(path_box_scores)
        for row in tqdm(box_scores, total=len(box_scores)):
            source = jhash(row)
            records = pd.DataFrame(row).to_dict(orient='records')
            records = list(map(lambda x: hash_and_stamp({**x, 'source': source}), records))
            mongodb.insert(
                database=conn,
                filter_fn=lambda record: dedup(seen, record),
                collection_name='raw_box_scores',
                records=records   
            )