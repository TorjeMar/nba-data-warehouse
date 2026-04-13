from _v2.utils.scraper import download

if __name__ == "__main__":
    player_ids = [...]

    download(
        ids=player_ids,
        url_fn=lambda player_id: f'https://www.nba.com/stats/player/{player_id}',
        output_directory='_data/000_raw/nba/player_data/data',
        inner_sleep_range=(1, 3),
        outer_sleep_range=(1, 5),
        path_processing_script='_data/000_raw/nba/player_data/download.py',
        path_input_data=None,
        is_directory_input=False
    )

