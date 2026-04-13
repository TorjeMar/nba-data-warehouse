import pandas as pd
from itertools import chain
from src.utils import disk


def get_tricodes_by_team_id(
    subset: pd.DataFrame,
    key_team_id: str,
    key_tricode: str,
):
    return  (
        subset
        .groupby(key_team_id)
        [key_tricode]
        .apply(list)
        .reset_index()
        .rename(columns={
            key_team_id: 'team_id',
            key_tricode: 'tricodes',
        })
    )

def select_tricode_by_latest_date(
    game: pd.DataFrame,
    key_team_id: str,
    key_tricode: str,
):
    selector = lambda df: (
        df
        .sort_values('game_date', ascending=False)
        .iloc[0]
    )

    return (
        game
        .groupby(key_team_id)
        [[key_tricode, 'game_date']]
        .apply(selector)
        .reset_index()
        .rename(columns={
            key_team_id: 'team_id',
            key_tricode: 'tricode',
        })
    )


def team_mapping_processor(
    json_path_game_dimension: str,
    json_path_team_dimension: str,
) -> list[dict]:
    
    team = pd.read_json(json_path_team_dimension)
    game = pd.read_json(json_path_game_dimension)


    tricodes_nba_teams = team.team_tricode.unique()
    home_nba_team = game[game.home_team_tricode.isin(tricodes_nba_teams)]
    away_nba_team = game[game.away_team_tricode.isin(tricodes_nba_teams)]
    nba_team_ids = set(home_nba_team.home_team_id.unique()) | set(away_nba_team.away_team_id.unique())


    subset_home = game[['home_team_tricode', 'home_team_id', 'game_date']].drop_duplicates()
    subset_away = game[['away_team_tricode', 'away_team_id', 'game_date']].drop_duplicates()

    combined_subset = pd.concat([
        subset_home.rename(columns={
            'home_team_tricode': 'team_tricode',
            'home_team_id': 'team_id',
        }),
        subset_away.rename(columns={
            'away_team_tricode': 'team_tricode',
            'away_team_id': 'team_id',
        }),
    ], ignore_index=True).drop_duplicates()

    last_seen_date_by_tricode = (
        combined_subset
        .groupby('team_tricode')['game_date']
        .max()
        .reset_index()
        .rename(columns={
            'team_tricode': 'tricode',
        })
        .set_index('tricode')
    )
    
    first_seen_date_by_tricode = (
        combined_subset
        .groupby('team_tricode')['game_date']
        .min()
        .reset_index()
        .rename(columns={
            'team_tricode': 'tricode',
        })
        .set_index('tricode')
    )

    tricode_by_date = select_tricode_by_latest_date(
        combined_subset,
        key_team_id='team_id',
        key_tricode='team_tricode',
    )

    tricodes_by_team_id = get_tricodes_by_team_id(
        combined_subset,
        key_team_id='team_id',
        key_tricode='team_tricode'
    )

    historic_tricodes = (
        tricodes_by_team_id
        .groupby('team_id')['tricodes']
        .apply(lambda x: set(chain.from_iterable(x)))
        .reset_index()
        .rename(columns={'tricodes': 'historic_tricode'})
    )

    tricodes = (
        tricode_by_date[['team_id', 'tricode']]
        .merge(historic_tricodes, on='team_id', how='left')
        .reset_index(drop=True)
        .rename(columns={
            'tricode': 'current_tricode',
        })
        .sort_values('team_id')
    )

    
    tricodes['is_nba_team'] = tricodes.team_id.isin(nba_team_ids)
    
    tricode_map = (
        tricodes
        .explode('historic_tricode')
        .reset_index(drop=True)
        .rename(columns={
            'historic_tricode': 'tricode',
        })
    )
    
    tricode_map['is_current_alias'] = tricode_map.pop('current_tricode') == tricode_map.tricode
    tricode_map['valid_since_date'] = first_seen_date_by_tricode.loc[tricode_map.tricode, 'game_date'].values
    tricode_map['valid_until_date'] = None
    tricode_map['first_seen_game_date'] = first_seen_date_by_tricode.loc[tricode_map.tricode, 'game_date'].values
    tricode_map['last_seen_game_date'] = last_seen_date_by_tricode.loc[tricode_map.tricode, 'game_date'].values
    
    tricodes.pop('historic_tricode')

    # print(tricode_map.to_string(line_width=400, col_space=20))
    # print('---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------')
    # print(tricodes.to_string(line_width=400, col_space=20))

    team_current_tricode = tricodes.to_dict(orient='records')
    team_tricode_history = tricode_map.to_dict(orient='records')
    return team_current_tricode, team_tricode_history

if __name__ == '__main__':
    current_tricode, tricode_history = team_mapping_processor(
        json_path_game_dimension='_data/001_staged/games/001_dimension/game.json',
        json_path_team_dimension='_data/001_staged/teams/001_dimension/team.json',
    )

    disk.write_json('_data/001_staged/teams/002_support/tricode_current.json', current_tricode)
    disk.write_json('_data/001_staged/teams/002_support/tricode_history.json', tricode_history)

