import json
import os
import xml.etree.ElementTree as elTree
from typing import Any, Dict

from boltons.strutils import slugify


class Process:

    def __init__(self, election_code: str, raw_file: str, input_file: str, output_file: str):
        this_dir = os.path.dirname(os.path.abspath(__file__))

        raw_data = self.load_raw(os.path.join(this_dir, 'raw', raw_file))
        input_data = self.load_input(os.path.join(this_dir, input_file))
        result = self.build(election_code, input_data, raw_data)

        output_path = os.path.join(this_dir, output_file)
        with open(output_path, 'wt') as f:
            json.dump(result, f, sort_keys=True, indent=2)

    def load_input(self, path: str) -> Dict[str, Any]:
        with open(path) as f:
            return json.load(f)

    def load_raw(self, path: str):
        tree = elTree.parse(path)
        root = tree.getroot()
        return root

    def build(self, election_code: str, input_data: Dict[str, Any], raw_data):
        unknown_name = '(Unknown)'
        assembly_abbr = 'l'

        result = {
            'election': {
                'code': election_code,
                'title': raw_data.attrib['name'],
                'country': 'Australia',
                'institution': 'Parliament of Australia',
                'description': '',
                'locality_name': '',
                'administrative_area_name': 'Federal',
                'year': 2017,
                'month': 11,
                'day': 0,
                'assembly_codes': [],
                'party_codes': [],
                'links': {},
            },
            'assemblies': [{
                'code': self._create_code(election_code, assembly_abbr),
                'title': 'Legislative Assembly of Queensland',
                'election_code': election_code,
                'electorate_codes': [],
                'description': '',
                'links': {},
            }],
            'electorates': [],
            'ballots': [],
            'parties': [],
            'candidates': [],
        }

        election = result['election']
        assembly = result['assemblies'][0]

        print('Building data for {}'.format(election_code))

        for party_item in raw_data.find('parties'):
            party_code = self._create_code(election_code, party_item.get('code'))
            party_name = party_item.get('name').title()

            result['parties'].append({
                'election_code': election_code,
                'code': party_code,
                'title': party_name or unknown_name,
                'candidate_codes': [],
                'description': '',
                'links': {},
            })

        # add items to the respective lists if the items doesn't already exist
        for district in raw_data.find('districts'):
            name = district.get('name').title()

            for candidate in district.find('candidates'):
                ballot_order_number = candidate.get('ballotOrderNumber')
                party_name = candidate.get('party')
                name_first = candidate.find('givenNames').text
                name_last = candidate.find('surname').text

                assembly_code = self._create_code(election_code, assembly_abbr)
                electorate_code = self._create_code(assembly_code, name or 'electorate-unknown')
                party_code = self._create_code(election_code, party_name or 'party-unknown')
                ballot_code = self._create_code(electorate_code, ballot_order_number or 'ballot-unknown')
                candidate_code = self._create_code(ballot_code, name_last, name_first or 'name-unknown')

                party = next(i for i in result['parties'] if i['code'] == party_code)

                if all(i['code'] != electorate_code for i in result['electorates']):
                    electorate = {
                        'code': electorate_code,
                        'title': name or unknown_name,
                        'election_code': election_code,
                        'description': '',
                        'assembly_code': assembly_code,
                        'candidate_codes': [],
                        'links': {},
                    }
                    result['electorates'].append(electorate)
                else:
                    electorate = next(i for i in result['electorates'] if i['code'] == electorate_code)

                if all(i['code'] != ballot_code for i in result['ballots']):
                    result['ballots'].append({
                        'code': ballot_code,
                        'election_code': election_code,
                        'assembly_code': assembly_code,
                        'electorate_code': electorate_code,
                        'candidate_code': candidate_code,
                        'party_code': party_code,
                        'position': ballot_order_number
                    })

                if all(i['code'] != candidate_code for i in result['candidates']):
                    result['candidates'].append({
                        'code': candidate_code,
                        'election_code': election_code,
                        'assembly_code': assembly_code,
                        'electorate_code': electorate_code,
                        'ballot_code': ballot_code,
                        'party_code': party_code,
                        'name_last': (name_last or '').title() or unknown_name,
                        'name_first': (name_first or '').title(),
                        'description': '',
                        'links': {},
                    })

                # add the codes to the respective lists
                if assembly_code not in election['assembly_codes']:
                    election['assembly_codes'].append(assembly_code)

                if party_code not in election['party_codes']:
                    election['party_codes'].append(party_code)

                if electorate_code not in assembly['electorate_codes']:
                    assembly['electorate_codes'].append(electorate_code)

                if candidate_code not in electorate['candidate_codes']:
                    electorate['candidate_codes'].append(candidate_code)

                if candidate_code not in party['candidate_codes']:
                    party['candidate_codes'].append(candidate_code)

        print('Finished')

        return result

    def _tidy(self, item):
        result = list(set(i for i in item if i))
        result.sort()
        return result

    def _create_code(self, *args):
        result = slugify('-'.join([i for i in args if i]), delim='-')
        return result


Process(
    'au-qld-2017-11',
    'publicResults.xml',
    'input.json',
    'data.json'
)

Process(
    'au-qld-2015-01',
    '../../au-qld-2015-01/raw/publicResults.xml',
    '../au-qld-2015-01/input.json',
    '../au-qld-2015-01/data.json'
)
