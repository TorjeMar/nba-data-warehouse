import requests
import traceback
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import TypedDict, Any
from types import MappingProxyType
from src.utils import disk
from src.utils.wrapper import exception_handler as exception_handler

BASE_HEADERS = MappingProxyType({
    "accept": "*/*",
    "accept-language": "nb-NO,nb;q=0.9,no;q=0.8,nn;q=0.7,en-US;q=0.6,en;q=0.5",
    "cache-control": "no-cache",
    "origin": "https://www.nba.com",
    "pragma": "no-cache",
    "referer": "https://www.nba.com/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
})

class Response(TypedDict):
    timestamp: str
    metadata: dict[str, Any]
    status_code: int
    headers: dict[str, Any]
    body: dict[str, Any] | str

@dataclass
class RequestResult:
    response: Response
    status_code: int

@dataclass
class Context:
    error_log: str

ctx = Context(error_log=None)

exception_kwargs = {
    'silent': True, 
    'callback': lambda log: disk.write_jsonl(
        ctx.error_log, log, default=str
    )
}

def timestamp():
    return datetime.now(timezone.utc).isoformat()

def safe_response_json_extract(rsp: requests.Response, **metadata) -> RequestResult:
    try:
        body = {
            'type': 'json',
            'data': rsp.json(),
            'error': None
        }
    except Exception as e:
        body = {
            'type': 'text',
            'data': rsp.text,
            'error': {
                'exception': e.__class__.__name__,
                'message': str(e),
                'traceback': traceback.format_exc(),
                'timestamp': timestamp(),
            }
        }
    
    return RequestResult(
        response={
            'timestamp': timestamp(),
            'metadata': metadata,
            'status_code': rsp.status_code,
            'headers': dict(rsp.headers),
            'body': body
        },
        status_code=rsp.status_code
    )
    

@exception_handler(**exception_kwargs)
def get_player_index(session: requests.Session, league_id, season, season_type, timeout: int = 300):
    # https://www.nba.com/players
    url = 'https://stats.nba.com/stats/playerindex?College=&Country=&DraftPick=&DraftRound=&DraftYear=&Height=&Historical=1&LeagueID=00&Season=2025-26&SeasonType=Regular%20Season&TeamID=0&Weight='
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        league_id=league_id,
        season=season,
        season_type=season_type,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_player_movement(session: requests.Session, timeout: int = 300):
    # https://www.nba.com/players/transactions
    url = 'https://stats.nba.com/js/data/playermovement/NBA_Player_Movement.json'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_league_game_log(session: requests.Session, timeout: int = 300):
    # https://www.nba.com/stats/players/boxscores
    url = 'https://stats.nba.com/stats/leaguegamelog?Counter=1000&DateFrom=&DateTo=&Direction=DESC&ISTRound=&LeagueID=00&PlayerOrTeam=P&Season=2025-26&SeasonType=Regular%20Season&Sorter=DATE'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_league_standings_per_team(session: requests.Session, timeout: int = 300):
    # https://www.nba.com/stats/teams/boxscores
    url = 'https://stats.nba.com/stats/leaguestandingsv3?Conference=&DateFrom=&DateTo=&Division=&GameScope=&GameSegment=&Height=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season=2025-26&SeasonSegment=&SeasonType=Pre%20Season&ShotClockRange=&StarterBench=&TeamID=0&TwoWay=0&VsConference=&VsDivision='
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_league_dash_team_stats(session: requests.Session, timeout: int = 300):
    # https://www.nba.com/stats/teams/boxscores
    url = 'https://stats.nba.com/stats/leaguedashteamstats?Conference=&DateFrom=&DateTo=&Division=&GameScope=&GameSegment=&Height=&LastNGames=0&LeagueID=00&Location=&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season=2025-26&SeasonSegment=&SeasonType=Pre%20Season&ShotClockRange=&StarterBench=&TeamID=0&TwoWay=0&VsConference=&VsDivision='
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_team_data(session: requests.Session, team_id: str, timeout: int = 300):
    # https://www.nba.com/team/1610612738/celtics
    url = f'https://www.nba.com/team/{team_id}'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_league_dash_lineups(session: requests.Session, timeout: int = 300):
    # https://www.nba.com/stats/lineups/traditional
    url = 'https://stats.nba.com/stats/leaguedashlineups?Conference=&DateFrom=&DateTo=&Division=&GameSegment=&GroupQuantity=5&ISTRound=&LastNGames=0&LeagueID=00&Location=&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlusMinus=N&Rank=N&Season=2025-26&SeasonSegment=&SeasonType=Regular%20Season&ShotClockRange=&TeamID=0&VsConference=&VsDivision='
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_box_score_summary(session: requests.Session, game_id: str, timeout: int = 300):
    # https://www.nba.com/inside-the-game
    url = f'https://stats.nba.com/stats/boxscoresummaryv3?GameID={game_id}&LeagueID=00'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_box_score_summary(session: requests.Session, game_id: str, timeout: int = 300):
    # https://www.nba.com/inside-the-game
    url = f'https://stats.nba.com/stats/boxscoresummaryv3?GameID={game_id}&LeagueID=00'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_shot_quality_shot_logs(session: requests.Session, game_id: str, timeout: int = 300):
    # https://www.nba.com/inside-the-game
    url = f'https://stats.nba.com/stats/shotqualityshotlog?GameID={game_id}&LeagueID=00'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_defensive_box_score(session: requests.Session, game_id: str, timeout: int = 300):
    # https://www.nba.com/inside-the-game
    url = f'https://stats.nba.com/stats/defensiveboxscore?GameID={game_id}'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_draft_history(session: requests.Session, game_id: str, timeout: int = 300):
    # https://www.nba.com/stats/draft/combine
    url = f'https://stats.nba.com/stats/drafthistory?College=&LeagueID=00&OverallPick=&RoundNum=&RoundPick=&Season=&TeamID=0&TopX='
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_draft_combine_player_anthro(session: requests.Session, game_id: str, timeout: int = 300):
    # https://www.nba.com/stats/draft/combine
    # @ 2025-26 : 2000-01
    url = f'https://stats.nba.com/stats/draftcombineplayeranthro?LeagueID=00&SeasonYear=2025-26&default=2025-26&initial=2025-26&seasonRange=1947%2C2025'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_draft_combine_strength_and_agility_results(session: requests.Session, game_id: str, timeout: int = 300):
    # https://www.nba.com/stats/draft/combine
    # @ 2025-26 : 2000-01
    url = f'https://stats.nba.com/stats/draftcombinedrillresults?LeagueID=00&SeasonYear=2025-26&default=2025-26&initial=2025-26&seasonRange=1947%2C2025'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_draft_combine_shooting_drills(session: requests.Session, game_id: str, timeout: int = 300):
    # https://www.nba.com/stats/draft/combine
    # @ 2025 : 2021
    url = f'https://cdn.nba.com/static/json/liveData/draftcombine/draftcombineshooting_2025.json'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_draft_combine_non_stationary_shooting(session: requests.Session, game_id: str, timeout: int = 300):
    # https://www.nba.com/stats/draft/combine
    # @ 2019-20 : 2014-15
    url = f'https://stats.nba.com/stats/draftcombinenonstationaryshooting?LeagueID=00&SeasonYear=2019-20'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_draft_combine_spot_up_shooting(session: requests.Session, game_id: str, timeout: int = 300):
    # https://www.nba.com/stats/draft/combine-spot-up
    # @ 2019-20 : 2014-15
    url = f'https://stats.nba.com/stats/draftcombinespotshooting?LeagueID=00&SeasonYear=2019-20'
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

@exception_handler(**exception_kwargs)
def get_player_violations_per_game(session: requests.Session, game_id: str, timeout: int = 300):
    # https://www.nba.com/stats/players/violations?PerMode=PerGame
    url = f'https://stats.nba.com/stats/leaguedashplayerstats?College=&Conference=&Country=&DateFrom=&DateTo=&Division=&DraftPick=&DraftYear=&GameScope=&GameSegment=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&MeasureType=Violations&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season=2025-26&SeasonSegment=&SeasonType=Regular%20Season&ShotClockRange=&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight='
    rsp = session.get(url, timeout=timeout)
    return safe_response_json_extract(
        rsp=rsp,
        url=url,
        request_kwargs={"timeout": timeout},
    )

