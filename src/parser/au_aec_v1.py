import csv
import json
from typing import Dict, List, Any

from boltons.strutils import slugify

from src.format.au_abs_pop_v1 import AuAbsPopV1
from src.format.au_aec_candidates_v1 import AuAecCandidatesV1
from src.format.au_aec_media_feed_standard_verbose_v1 import (
    AuAecMediaFeedStandardVerboseV1,
)
from src.format.au_aec_tally_room_v1 import AuAecTallyRoomV1
from src.helper.aec import AEC
from src.helper.general import General
from src.model.combination import Combination
from src.model.election import Election


class AuAecV1:
    def __init__(self, general: General):
        self._general = general
        self._aec = AEC()

    def load_input(self, path: str) -> Dict[str, Any]:
        with open(path) as f:
            return json.load(f)

    def load_raw(self, path: str) -> List[Dict[str, Any]]:
        with open(path) as f:
            reader = csv.DictReader(f)
            result = []
            for row in reader:
                result.append(row)
            return result

    def build(
        self,
        election_code: str,
        input_data: Dict[str, Any],
        raw_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        result = {
            "election": {},
            "assemblies": [],
            "electorates": [],
            "ballots": [],
            "parties": [],
            "candidates": [],
        }

        print("Building data for {}".format(election_code))

        unknown_name = "(Unknown)"

        for row in raw_data:
            # create the various codes for the data items
            assembly_code = self._create_code(
                election_code, row["nom_ty"] or "assembly-unknown"
            )
            electorate_code = self._create_code(
                assembly_code, row["state_ab"] or "electorate-unknown", row["div_nm"]
            )
            party_code = self._create_code(
                election_code, row["party_ballot_nm"] or "party-unknown"
            )
            ballot_code = self._create_code(
                electorate_code,
                row["ticket"],
                row["ballot_position"] or "ballot-unknown",
            )
            candidate_code = self._create_code(
                ballot_code, row["surname"], row["ballot_given_nm"] or "name-unknown"
            )

            # add items to the respective lists if the items doesn't already exist
            if "code" not in result["election"]:
                result["election"] = {
                    "code": election_code,
                    "title": row["txn_nm"],
                    "country": "Australia",
                    "institution": "Parliament of Australia",
                    "description": "",
                    "locality_name": "",
                    "administrative_area_name": "Federal",
                    "year": 2016,
                    "month": 7,
                    "day": 2,
                    "assembly_codes": [],
                    "party_codes": [],
                    "links": {},
                }
            election = result["election"]

            if all(i["code"] != assembly_code for i in result["assemblies"]):
                assembly = {
                    "code": assembly_code,
                    "title": (
                        "House of Representatives"
                        if assembly_code.endswith("h")
                        else "Senate"
                    ),
                    "election_code": election_code,
                    "electorate_codes": [],
                    "description": "",
                    "links": {},
                }
                result["assemblies"].append(assembly)
            else:
                assembly = next(
                    i for i in result["assemblies"] if i["code"] == assembly_code
                )

            if all(i["code"] != electorate_code for i in result["electorates"]):
                electorate = {
                    "code": electorate_code,
                    "title": row["div_nm"] or row["state_ab"] or unknown_name,
                    "election_code": election_code,
                    "description": "",
                    "assembly_code": assembly_code,
                    "candidate_codes": [],
                    "links": {},
                }
                result["electorates"].append(electorate)
            else:
                electorate = next(
                    i for i in result["electorates"] if i["code"] == electorate_code
                )

            if all(i["code"] != ballot_code for i in result["ballots"]):
                result["ballots"].append(
                    {
                        "code": ballot_code,
                        "election_code": election_code,
                        "assembly_code": assembly_code,
                        "electorate_code": electorate_code,
                        "candidate_code": candidate_code,
                        "party_code": party_code,
                        "position": row["ballot_position"],
                        "name": row["div_nm"] or row["ticket"] or unknown_name,
                    }
                )

            if all(i["code"] != party_code for i in result["parties"]):
                party = {
                    "election_code": election_code,
                    "code": party_code,
                    "title": row["party_ballot_nm"] or unknown_name,
                    "candidate_codes": [],
                    "description": "",
                    "links": {},
                }
                result["parties"].append(party)
            else:
                party = next(i for i in result["parties"] if i["code"] == party_code)

            if all(i["code"] != candidate_code for i in result["candidates"]):
                result["candidates"].append(
                    {
                        "code": candidate_code,
                        "election_code": election_code,
                        "assembly_code": assembly_code,
                        "electorate_code": electorate_code,
                        "ballot_code": ballot_code,
                        "party_code": party_code,
                        "name_last": (row["surname"] or "").title() or unknown_name,
                        "name_first": (row["ballot_given_nm"] or "").title(),
                        "occupation": row["occupation"],
                        "address": ", ".join(
                            [
                                i
                                for i in [
                                    row["address_1"],
                                    row["address_2"],
                                    (row["suburb"] or "").title(),
                                    row["address_state_ab"],
                                    row["postcode"],
                                ]
                                if i
                            ]
                        ),
                        "post": ", ".join(
                            [
                                i
                                for i in [
                                    row["postal_address_1"],
                                    row["postal_address_2"],
                                    (row["postal_suburb"] or "").title(),
                                    row["postal_state_ab"],
                                    row["postal_postcode"],
                                ]
                                if i
                            ]
                        ),
                        "phone_work": (row["contact_work_ph"] or "").lower(),
                        "phone_home": (row["contact_home_ph"] or "").lower(),
                        "phone_mobile": (row["contact_mobile_no"] or "").lower(),
                        "fax": (row["contact_fax"] or "").lower(),
                        "email": (row["contact_email"] or "").lower(),
                        "description": "",
                        "links": {},
                    }
                )

            # add the codes to the respective lists
            if assembly_code not in election["assembly_codes"]:
                election["assembly_codes"].append(assembly_code)

            if party_code not in election["party_codes"]:
                election["party_codes"].append(party_code)

            if electorate_code not in assembly["electorate_codes"]:
                assembly["electorate_codes"].append(electorate_code)

            if candidate_code not in electorate["candidate_codes"]:
                electorate["candidate_codes"].append(candidate_code)

            if candidate_code not in party["candidate_codes"]:
                party["candidate_codes"].append(candidate_code)

        # then use the input data to further populate the result
        for k, v in input_data.items():
            if k == "election":
                continue
            for i in input_data[k]:
                raise

        print("Finished")

        return result

    def _tidy(self, item):
        result = list(set(i for i in item if i))
        result.sort()
        return result

    def _create_code(self, *args):
        result = slugify("-".join([i for i in args if i]), delim="-")
        return result

    def populate(
        self, original_data: dict, combination: Combination, election: Election
    ) -> None:
        """Populate the Combination with election data."""

        gen = self._general
        aec = self._aec

        media_feed = AuAecMediaFeedStandardVerboseV1(gen, aec)
        tally_room = AuAecTallyRoomV1(gen, aec)
        abs_pop = AuAbsPopV1(gen, aec)
        candidates = AuAecCandidatesV1(gen, aec)

        orig = original_data
        comb = combination
        elec = election

        media_feed.populate(orig, comb, elec)
        tally_room.populate(orig, comb, elec)
        abs_pop.populate(orig, comb, elec)
        candidates.populate(orig, comb, elec)


# Process(
#     "au-2016-07",
#     "2016federalelection-all-candidates-nat-30-06-924.csv",
#     "../../raw/2016-07-02-au/input.json",
#     "../2016-07-02-au/data.json",
# )
#
# Process(
#     "au-2019-05",
#     "../../au-2019-05/raw/2019federalelection-all-candidates-nat-30-04.csv",
#     "../au-2019-05/input.json",
#     "../au-2019-05/data.json",
# )
