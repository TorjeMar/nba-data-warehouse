from uuid import uuid4
from itertools import chain

from src.utils import disk
from src.utils import debug
from src.processing.ids import id_mapper, IDMapper

def construct_team_dimension(leauge_hiearchy: dict, id_mapper: IDMapper, preserve: tuple[str] = None) -> tuple[list, list, list, dict]:
    preserve = preserve or ()

    # ------------------------
    # Helper function to explode values on multiple delimiters and preserve certain values
    # ------------------------    
    def explode(output_key: str, key: str, obj: dict, **kwargs):
        split_on = (',', ' and ', '&')
        value = obj.get(key, '')
        if not value:
            return []
        
        if value in preserve or not isinstance(value, str):
            return [dict(**kwargs, **{output_key: value})]
        
        values: list[str] = [[value]]
        for splitter in split_on:
            values = chain.from_iterable(values)
            values = list(map(lambda v: v.split(splitter), values))
        
        values = chain.from_iterable(values)
        values = map(lambda v: v.strip(), values)
        values = filter(lambda v: v, values)
        return list(map(lambda v: dict(**kwargs, **{output_key: v}), values))

    # ------------------------
    # Main logic to construct teams, team roles, and team facts
    # ------------------------
    teams = []
    roles = []
    facts = []

    conferences = leauge_hiearchy['conferences']
    for conference in conferences:
        c_id = id_mapper(
            namespace='conference',
            key=conference['alias'],
            provider='sportsradar',
            provider_id=conference['id'],
            custom_id=str(uuid4()),
        )

        for division in conference['divisions']:
            d_id = id_mapper(
                namespace='division',
                key=division['alias'],
                provider='sportsradar',
                provider_id=division['id'],
                custom_id=str(uuid4()),
            )

            for team in division['teams']:
                t_id = id_mapper(
                    namespace='team',
                    key=team['alias'],
                    provider='sportsradar',
                    provider_id=team['id'],
                    custom_id=str(uuid4()),
                )
                
                venue = team['venue']

                meta = dict(
                    team_id=t_id,
                    team_name=team['name'],
                    team_alias=team['alias'],
                    team_tricode=team['alias'],
                )

                teams.append(dict(
                    **meta,
                    team_market=team['market'],
                    division_id=d_id,
                    division_name=division['name'],
                    division_alias=division['alias'],
                    conference_id=c_id,
                    conference_name=conference['name'],
                    conference_alias=conference['alias'],
                    founded_in=team['founded'],
                    venue_name=venue['name'],
                    venue_capacity=venue['capacity'],
                    venue_address=venue['address'],
                    venue_city=venue['city'],
                    venue_state=venue['state'],
                    venue_zip=venue['zip'],
                    venue_country=venue['country'],
                ))


                roles.extend(chain.from_iterable(map(
                    lambda role: explode('name', role, team, **meta, role=role), 
                    [
                        'mascot',
                        'sponsor',
                        'owner',
                        'general_manager',
                    ]
                )))
    
                facts.extend(chain.from_iterable(map(
                    lambda fact: explode('value', fact, team, **meta, fact=fact),
                    [
                        'championships_won',
                        'championship_seasons',
                        'playoff_appearances',
                        'conference_titles',
                        'division_titles',
                    ]
                )))


    return teams, roles, facts


if __name__ == '__main__':
    league_hiarchy = '_sources/sportsradar/leaugeHiearchy.json'
    lh = disk.read_json(league_hiarchy)

    id_mapper.from_disk()
    teams, team_roles, team_facts = construct_team_dimension(
        leauge_hiearchy=lh, 
        id_mapper=id_mapper, 
        preserve=("Kroenke Sports & Entertainment", )
    )
    id_mapper.to_disk()

    disk.write_json('_data/001_staged/teams/001_dimension/team.json', teams)
    disk.write_json('_data/001_staged/teams/002_support/roles.json', team_roles)
    disk.write_json('_data/001_staged/teams/003_fact/fact.json', team_facts)
