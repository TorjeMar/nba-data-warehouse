from uuid import uuid4
from itertools import chain

from src.utils import disk, jhash
from src.utils import debug
from src.processing.ids import id_mapper, IDMapper
from copy import deepcopy

def construct_prospect_dimension(prospects_directory: str, id_mapper: IDMapper) -> tuple[list[dict], list[dict]]:
    # TODO: Ignored fields draft/venue, draft/start_date, draft/end_date, draft/league

    
    college_teams = dict()
    otther_teams = dict()
    prospects = []

    # --------------------------
    # Helper function to construct entries for conference, division, and team
    # --------------------------
    def to_entry(namespace: str, prefix: str, obj: dict, mappings: str, provider: str, provider_id: str) -> dict:
        entry = {}
        alias = obj.get('alias')
        kwargs = {k: obj.get(k) for k in mappings}

        if alias:
            obj_id = id_mapper(namespace, alias, provider, provider_id, str(uuid4()))
            entry = {
                f'{prefix}_id': obj_id,
                f'{prefix}_alias': alias,
                **{f'{prefix}_{k}': v for k, v in kwargs.items()}
            }

        return entry


    for prospect_data in list(map(disk.read_json, disk.listdir(prospects_directory))):
        
        pr = prospect_data['body']['data']
        list_of_prospects: list[dict] = pr['prospects']
        draft_year = pr['draft']['year']

        for prospect in list_of_prospects:
            # --------------------------
            # Construct entries for conference, division, and team
            # --------------------------
            team_name: str = prospect.pop('team_name', '')
            high_school: dict = prospect.pop('high_school', '')
            conference: dict = prospect.pop('conference', {})
            division: dict = prospect.pop('division', {})
            team: dict = prospect.pop('team', {})

            affiliate_organization = {}
            affiliate_organization_type = None

            if team and conference and division:
                affiliate_organization_type = 'us_college_team'

                conference_entry = to_entry(
                    namespace='us_college_conference',
                    prefix='conference',
                    obj=conference,
                    mappings=('name', ),
                    provider='sportsradar',
                    provider_id=conference.get('id'),
                )
                
                division_entry = to_entry(
                    namespace='us_college_division',
                    prefix='division',
                    obj=division,
                    mappings=('name', ),
                    provider='sportsradar',
                    provider_id=division.get('id'),
                )

                team_entry = to_entry(
                    namespace='us_college_team',
                    prefix='organization',
                    obj=team,
                    mappings=('name', ),
                    provider='sportsradar',
                    provider_id=team.get('id'),
                )

                affiliate_organization = {
                    **team_entry, 
                    'organization_type': affiliate_organization_type,
                    **division_entry, 
                    **conference_entry,
                }

                college_teams[jhash(affiliate_organization)] = affiliate_organization
            
            elif team_name:
                affiliate_organization_type = 'other_organization'

                team_entry = to_entry(
                    namespace='other_organization',
                    prefix='organization',
                    obj={'alias': team_name, 'name': high_school or team_name},
                    mappings=('name', ),
                    provider='sportsradar',
                    provider_id=team_name,
                )

                affiliate_organization = {
                    **team_entry,
                    'organization_type': affiliate_organization_type,
                }

                otther_teams[jhash(affiliate_organization)] = affiliate_organization

            else:
                print(f"Prospect {prospect['name']} has no team or team name information. Skipping affiliate organization construction.")
            

            # --------------------------
            # Construct prospect entry
            # --------------------------
            prospect.pop('source_id', None)

            birthplace = prospect.pop('birth_place', '').split(',')
            birthplace = zip(('city', 'state', 'country'), birthplace)
            birthplace = {f'birth_{k}':v.strip() or None for k, v in birthplace}
            
            p_id = id_mapper('prospect', prospect['name'], 'sportsradar', prospect.pop('id'), str(uuid4()))
            
            prospects.append({
                'prospect_id': p_id,
                'draft_year': draft_year,
                **prospect,
                **birthplace,
                'affiliate_organization': affiliate_organization.get('organization_id', None),
                'affiliate_organization_type': affiliate_organization_type,
            })

    return prospects, [v for v in college_teams.values() if v], [v for v in otther_teams.values() if v]


if __name__ == '__main__':
    prospects = '_sources/sportsradar/prospects.json'
    prospects = disk.read_json(prospects)

    id_mapper.from_disk()
    prospects, us_college_organizations, other_organizations = construct_prospect_dimension(
        prospects_directory='_data/000_raw/sportradar/drafts/prospects/data', 
        id_mapper=id_mapper, 
    )
    id_mapper.to_disk()

    disk.write_json('_data/001_staged/prospects/001_dimension/prospect.json', prospects)
    disk.write_json('_data/001_staged/organizations/001_dimension/us_college_organization.json', us_college_organizations)
    disk.write_json('_data/001_staged/organizations/001_dimension/other_organization.json', other_organizations)

