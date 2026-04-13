from _v2.utils.scraper import download
from src.utils import disk

if __name__ == "__main__":
    game_ids = [...]

    game_ids = disk.read_json('data/unique_game_ids.json')
    game_ids = game_ids[-1]['data']
    game_ids = [_['game_id'] for _ in game_ids]

    download(
        ids=game_ids,
        url_fn=lambda game_id: f'https://www.nba.com/game/{game_id}',
        output_directory='_data/000_raw/nba/game_data',
        inner_sleep_range=(0.1, 1),
        outer_sleep_range=(1, 3),
        path_processing_script='_data/000_raw/nba/game_data/download.py',
        path_input_data=None,
        is_directory_input=False,
    )

