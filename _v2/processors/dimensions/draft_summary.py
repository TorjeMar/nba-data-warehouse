from uuid import uuid4
from itertools import chain

from src.utils import disk, jhash
from src.utils import debug
from src.processing.ids import id_mapper, IDMapper
from copy import deepcopy

def construct_draft_dimension(directory: str, id_mapper: IDMapper) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    output = {
        'picks': [],
        'trades': [],
        'draft': [],
        'venues': [],
    }
    

    for file in disk.listdir(directory):
        if not file.endswith('.json'):
            continue

        draft_summary = disk.read_json(file)
        data = draft_summary['body']['data']
        draft = data['draft']
        rounds = data['rounds']
        year = draft['year']

        draft.pop('league', None)
        draft.pop('broadcast', None)
        venue = draft.pop('venue', {})

        venue_key = (
            venue.get('city', ''), 
            venue.get('state', ''), 
            venue.get('country', '')
        )

        venue = {
            'venue_id': id_mapper(
                namespace='venue', 
                key=venue_key, 
                provider='sportradar', 
                provider_id=venue['name'], 
                custom_id=str(uuid4())
            ),
            **venue,
        }

        draft = {
            'draft_id': id_mapper(
                namespace='draft', 
                key=f"{year}", 
                provider='sportradar', 
                provider_id=draft['id'], 
                custom_id=str(uuid4())
            ),
            'year': draft['year'],
            'start_date': draft['start_date'],
            'end_date': draft['end_date'],
            'status': draft['status'],
            'venue_id': venue['venue_id'],
        }

        output['draft'].append(draft)
        output['venues'].append(venue)

        for round in rounds:
            round_number = round['number']

            for pick in round['picks']:
                team = pick['team']
                player = pick['prospect']

                pick_number = pick['number']
                pick_overall = pick['overall']

                team_id = id_mapper(
                    namespace='organization', 
                    key=team['name'], 
                    provider='sportradar', 
                    provider_id=team['id'], 
                    custom_id=str(uuid4())
                )

                player_id = id_mapper(
                    namespace='prospect', 
                    key=player['name'], 
                    provider='sportradar', 
                    provider_id=player['id'], 
                    custom_id=str(uuid4())
                )

                pick_id = id_mapper(
                    namespace=f'draft_pick/{year}', 
                    key=pick_overall, 
                    provider='sportradar', 
                    provider_id=pick['id'], 
                    custom_id=str(uuid4())
                )

                output['picks'].append({
                    'pick_id': pick_id,
                    'team_id': team_id,
                    'draft_id': draft['draft_id'],
                    'player_id': player_id,
                    'round_number': round_number,
                    'pick_number': pick_number,
                    'pick_overall': pick_overall,
                })

                output['trades'].extend([
                    {
                        'trade_id': id_mapper(
                            namespace=f'draft_trade/{year}', 
                            key=trade['id'], 
                            provider='sportradar', 
                            provider_id=trade['id'], 
                            custom_id=str(uuid4())
                        )
                    }
                    for trade in pick.get('trades', [])
                ])


    return output['picks'], output['venues'], output['draft'], output['trades']

if __name__ == '__main__':

    id_mapper.from_disk()
    picks, venues, draft, trades = construct_draft_dimension(
        directory='_data/000_raw/sportradar/drafts/summary/data/', 
        id_mapper=id_mapper, 
    )
    id_mapper.to_disk()

    disk.write_json('_data/001_staged/drafts/003_fact/picks.json', picks)
    disk.write_json('_data/001_staged/drafts/001_dimension/draft.json', draft)
    disk.write_json('_data/001_staged/trades/001_dimension/trades.json', trades)
    disk.write_json('_data/001_staged/venues/001_dimension/venues.json', venues)

