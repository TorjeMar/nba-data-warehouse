import os
import dotenv
import requests
from typing import Literal
from dataclasses import dataclass
from types import MappingProxyType
from src.utils import disk
from src.utils.wrapper import exception_handler as exception_handler
from _v2.utils.requests import RequestContext, safe_response_json_extract

dotenv.load_dotenv()

BASE_URL_DRAFTS = 'https://api.sportradar.com/draft/nba/trial/v1/en'
BASE_URL_NBA = 'https://api.sportradar.com/nba/trial/v8/en'

BASE_HEADERS = MappingProxyType({
    'x-api-key': os.environ['SPORTSRADAR_API_KEY'],
    'accept': 'application/json'
})

ctx = RequestContext(error_log=None)

exception_kwargs = {
    'silent': True, 
    'callback': lambda log: disk.write_jsonl(
        ctx.error_log, log, default=str
    )
}

@exception_handler(**exception_kwargs)
def get_league_hierarchy(session: requests.Session, timeout: int = 300):
    # https://developer.sportradar.com/basketball/reference/nba-league-hierarchy
    url = f'{BASE_URL_NBA}/league/hierarchy.json'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_injuries(session: requests.Session, timeout: int = 300):
    # https://developer.sportradar.com/basketball/reference/nba-injuries
    url = f'{BASE_URL_NBA}/league/injuries.json'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_seasons(session: requests.Session, timeout: int = 300):
    # https://developer.sportradar.com/basketball/reference/nba-seasons
    url = f'{BASE_URL_NBA}/league/seasons.json'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_teams(session: requests.Session, timeout: int = 300):
    # https://developer.sportradar.com/basketball/reference/nba-teams
    url = f'{BASE_URL_NBA}/league/teams.json'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_team_profile(session: requests.Session, team_id: str, timeout: int = 300):
    if not isinstance(team_id, str) or len(team_id) == 0:
        raise ValueError(f'Invalid team_id: {team_id}. Must be a non-empty string.')

    # https://developer.sportradar.com/basketball/reference/nba-team-profile
    url = f'{BASE_URL_NBA}/teams/{team_id}/profile.json'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_schedule(session: requests.Session, season_year: int, season_type: Literal['PRE', 'REG', 'IST', 'PIT', 'PST'], timeout: int = 300):
    if not isinstance(season_year, int) or season_year < 2013 or season_year > 2025:
        raise ValueError(f'Invalid season_year: {season_year}. Must be an integer between 2013 and 2025.')

    if not isinstance(season_type, str) or season_type not in {'PRE', 'REG', 'IST', 'PIT', 'PST'}:
        raise ValueError(f'Invalid season_type: {season_type}. Must be one of PRE, REG, IST, PIT, PST.')

    # https://developer.sportradar.com/basketball/reference/nba-schedule
    url = f'{BASE_URL_NBA}/games/{season_year}/{season_type}/schedule.json'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_draft_prospects(session: requests.Session, draft_year: int, timeout: int = 300):
    if not isinstance(draft_year, int) or draft_year < 2019 or draft_year > 2025:
        raise ValueError(f'Invalid draft_year: {draft_year}. Must be an integer between 2019 and 2025.')
    
    # https://developer.sportradar.com/basketball/reference/nba-prospects
    url = f'{BASE_URL_DRAFTS}/{draft_year}/prospects.json'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        draft_year=draft_year,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_draft_summary(session: requests.Session, draft_year: int, timeout: int = 300):
    if not isinstance(draft_year, int) or draft_year < 2019 or draft_year > 2025:
        raise ValueError(f'Invalid draft_year: {draft_year}. Must be an integer between 2019 and 2025.')

    # https://developer.sportradar.com/basketball/reference/nba-draft-summary
    url = f'{BASE_URL_DRAFTS}/{draft_year}/draft.json'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        draft_year=draft_year,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_trades(session: requests.Session, draft_year: int, timeout: int = 300):
    if not isinstance(draft_year, int) or draft_year < 2019 or draft_year > 2025:
        raise ValueError(f'Invalid draft_year: {draft_year}. Must be an integer between 2019 and 2025.')

    # https://developer.sportradar.com/basketball/reference/nba-trades
    url = f'{BASE_URL_DRAFTS}/{draft_year}/trades.json'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        draft_year=draft_year,
        request_kwargs={"timeout": timeout},
    )


