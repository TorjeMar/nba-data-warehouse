import pandas as pd
from _v2.utils.scraper import download
from src.utils import disk  


if __name__ == "__main__":
    path_input_data = '_data/000_raw/nba/player_index/data/2025-26_Regular Season.json'
    data = disk.read_json(path_input_data)
    data = data['data']['body']['data']['resultSets'][0]
    data = pd.DataFrame(data['rowSet'], columns=data['headers'])

    team_ids = data.TEAM_ID.unique().tolist()

    print(f'Starting download of team data for {len(team_ids)} teams\n')
    confirm = input(f'Output directory: _data/000_raw/nba/team_data\n\nProceed? (y/n): ')
    if confirm.lower() != 'y':
        print('Aborting download.')
        exit()

    download(
        ids=team_ids,
        url_fn=lambda team_id: f'https://www.nba.com/stats/team/{team_id}',
        output_directory='_data/000_raw/nba/team_data',
        inner_sleep_range=(1, 3),
        outer_sleep_range=(1, 5),
        path_processing_script='_data/000_raw/nba/team_data/download.py',
        path_input_data=path_input_data,
        is_directory_input=False
    )

