import requests
from tqdm import tqdm
from src.utils import disk
from _v2.utils.requests import create_sleep_schedule_uniform
from _v2.utils.provenance import build_provenance_envelope
from _v2.sources.sportradar.endpoints import (
    BASE_HEADERS,
    get_league_hierarchy,
    get_team_profile, 
    get_teams,
    ctx
)

def download_team_profiles(output_dir: str):
    output_dir_profiles = disk.joinpath(output_dir, 'teams/data/profiles')
    output_path_league = disk.joinpath(output_dir, 'teams/data/league.json')
    output_path_teams = disk.joinpath(output_dir, 'teams/data/teams.json')
    ctx.error_log = disk.joinpath(output_dir, 'teams/error.jsonl')

    session = requests.Session()
    session.headers.update(BASE_HEADERS)

    disk.makedirs(output_dir_profiles, exist_ok=True)

    sleep_schedule = create_sleep_schedule_uniform(min_delay=1.0, max_delay=1.5)

    # -------------------------
    # Download Teams
    # -------------------------
    if not disk.isfile(output_path_teams):
        output = get_teams(session=session)
        if output.status_code == 200:
            envelope = build_provenance_envelope(
                source='sportradar',
                path_input_data=None,
                path_processing_script=__file__,
                is_directory_output=False,
                is_directory_input=False,
                data=output.response,
            )

            disk.write_json(output_path_teams, envelope)
        else:
            disk.write_jsonl(ctx.error_log, output.response)
            print(f'Failed to download teams data. Status code: {output.status_code}')
            print(f'Error details logged to {ctx.error_log}')
            return
    
    # -------------------------
    # Download League Hierarchy
    # -------------------------
    if not disk.isfile(output_path_league):
        output = get_league_hierarchy(session=session)
        if output.status_code == 200:
            envelope = build_provenance_envelope(
                source='sportradar',
                path_input_data=None,
                path_processing_script=__file__,
                is_directory_output=False,
                is_directory_input=False,
                data=output.response,
            )

            disk.write_json(output_path_league, envelope)
        else:
            disk.write_jsonl(ctx.error_log, output.response)
            print(f'Failed to download league hierarchy data. Status code: {output.status_code}')
            print(f'Error details logged to {ctx.error_log}')
            return
    

    sleep_schedule()

    league = disk.read_json(output_path_league)
    teams = [
        team
        for conf in league['body']['data']['conferences'] 
        for div in conf['divisions'] 
        for team in div['teams']
    ]


    # -------------------------
    # Download Team Profiles
    # -------------------------
    for team in tqdm(teams, desc="Downloading team profiles", total=len(teams)):
        team_id = team['id']

        output_path_profile = disk.joinpath(output_dir_profiles, f'{team_id}.json')

        if disk.isfile(output_path_profile):
            print(f'Profile for team_id {team_id} already exists, skipping download.')
            continue

        output = get_team_profile(session=session, team_id=team_id)
        if output.status_code == 200:
            envelope = build_provenance_envelope(
                source='sportradar',
                path_input_data=None,
                path_processing_script=__file__,
                is_directory_output=False,
                is_directory_input=False,
                data=output.response,
            )

            disk.write_json(output_path_profile, envelope)
        else:
            disk.write_jsonl(ctx.error_log, output.response)
            print(f'Failed to download profile for team_id {team_id}. Status code: {output.status_code}')
            print(f'Error details logged to {ctx.error_log}')

        sleep_schedule()


if __name__ == '__main__':
    download_team_profiles(output_dir='_data/000_raw/sportradar')


