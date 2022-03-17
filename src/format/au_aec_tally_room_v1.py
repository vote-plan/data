from typing import Callable

from src.helper.aec import AEC
from src.helper.general import General
from src.model.assembly import Assembly
from src.model.candidate import Candidate
from src.model.combination import Combination
from src.model.election import Election
from src.model.electorate import Electorate
from src.model.note import Note
from src.model.party import Party
from src.model.result import Result


class AuAecTallyRoomV1:
    """Australian Electoral Commission TallyRoom (v1)."""

    def __init__(self, general: General, aec: AEC):
        self._general = general
        self._aec = aec

        self._senate: Assembly = None
        self._house_reps: Assembly = None

        self._c_info = Note.get_category_raw_info()

    def populate(
        self, original_data: dict, combination: Combination, election: Election
    ) -> None:
        """Populate the Combination with election data."""

        self._senate = self._aec.get_assembly_senate(combination)
        self._house_reps = self._aec.get_assembly_house_reps(combination)

        aec_code = self._aec.election_code(election)
        items: dict[str, Callable[[list, Combination, Election], None]] = {
            f"GeneralEnrolmentByDivisionDownload-{aec_code}.csv": self._rows_enrolment_division,
            f"GeneralEnrolmentByStateDownload-{aec_code}.csv": self._rows_enrolment_state,
            f"GeneralPartyDetailsDownload-{aec_code}.csv": self._rows_party_details,
            f"HouseCandidatesDownload-{aec_code}.csv": self._rows_house_candidates,
            f"HouseDopByDivisionDownload-{aec_code}.csv": self._rows_house_distribution_preferences,
            f"HouseInformalByDivisionDownload-{aec_code}.csv": self._rows_house_informal_division,
            f"HouseInformalByStateDownload-{aec_code}.csv": self._rows_house_informal_state,
            f"HouseTurnoutByDivisionDownload-{aec_code}.csv": self._rows_house_turnout_division,
            f"HouseTurnoutByStateDownload-{aec_code}.csv": self._rows_house_turnout_state,
            f"HouseVotesCountedByDivisionDownload-{aec_code}.csv": self._rows_house_votes_division,
            f"HouseVotesCountedByStateDownload-{aec_code}.csv": self._rows_house_votes_state,
            f"SenateCandidatesDownload-{aec_code}.csv": self._rows_senate_candidates,
            f"SenateInformalByDivisionDownload-{aec_code}.csv": self._rows_senate_informal_division,
            f"SenateInformalByStateDownload-{aec_code}.csv": self._rows_senate_informal_state,
            f"SenateStateDOPDownload-{aec_code}-ACT.csv": self._rows_senate_distribution_preferences,
            f"SenateStateDOPDownload-{aec_code}-NSW.csv": self._rows_senate_distribution_preferences,
            f"SenateStateDOPDownload-{aec_code}-NT.csv": self._rows_senate_distribution_preferences,
            f"SenateStateDOPDownload-{aec_code}-QLD.csv": self._rows_senate_distribution_preferences,
            f"SenateStateDOPDownload-{aec_code}-SA.csv": self._rows_senate_distribution_preferences,
            f"SenateStateDOPDownload-{aec_code}-TAS.csv": self._rows_senate_distribution_preferences,
            f"SenateStateDOPDownload-{aec_code}-VIC.csv": self._rows_senate_distribution_preferences,
            f"SenateStateDOPDownload-{aec_code}-WA.csv": self._rows_senate_distribution_preferences,
            f"SenateTurnoutByDivisionDownload-{aec_code}.csv": self._rows_senate_turnout_division,
            f"SenateVotesCountedByDivisionDownload-{aec_code}.csv": self._rows_senate_votes_division,
            f"SenateVotesCountedByStateDownload-{aec_code}.csv": self._rows_senate_votes_state,
        }

        processed = set()
        for filename, process in items.items():
            data: list = original_data.get(filename)
            if data:
                process(data, combination, election)
                processed.add(filename)

        # check if anything was missed
        original_available = {
            k
            for k in original_data.keys()
            if f"-{aec_code}" in k and k.endswith(".csv")
        }
        missed = original_available - processed
        if missed:
            raise ValueError(f"Did not process '{missed}'.")

    # --------------------
    # Methods that know how to extract pieces of info about models.
    # --------------------

    def _info_electorate_title(self, item: dict):
        state_ab = item.get("StateAb") or item.get("State")
        state_name = item.get("StateNm")
        div_name = item.get("DivisionNm")
        div_id = item.get("DivisionID")

        title = div_name or state_ab
        title = self._general.electorate_title(title)
        if not title:
            raise ValueError("Electorate must have title.")
        return title

    def _info_electorate_code(self, assembly: Assembly, item: dict):
        title = self._info_electorate_title(item)
        code = self._general.electorate_code(assembly.code, title)
        if not code:
            raise ValueError("Electorate must have code.")
        return code

    def _info_result_electorate_code(self, assembly: Assembly, item: dict, suffix: str):
        title = self._info_electorate_title(item)
        result = self._general.result_electorate_code(assembly.code, title, suffix)
        return result

    def _info_party_short(self, item: dict):
        party_ab = item.get("PartyAb", "").strip()
        if party_ab:
            return party_ab
        else:
            return self._aec.get_party_independent_short()

    def _info_party_title(self, item: dict):
        party_name = item.get("PartyNm", "").strip()
        reg_ab = item.get("RegisteredPartyAb", "").strip()
        title = General.pick_longest_str(party_name, reg_ab)
        if title:
            return title
        else:
            return self._aec.get_party_independent_title()

    def _info_party_other_titles(self, item: dict):
        party_name = item.get("PartyNm", "").strip()
        reg_ab = item.get("RegisteredPartyAb", "").strip()

        title = self._info_party_title(item)
        other_title = reg_ab if title == party_name else party_name
        return other_title

    def _info_party_code(self, election: Election, item: dict):
        title = self._info_party_title(item)
        return self._general.party_code(election.code, title)

    def _info_party_category(self, item: dict):
        party_ab = item.get("PartyAb", "").strip()
        has_party_ab = "PartyAb" in item
        party_name = item.get("PartyNm", "").strip()
        has_party_name = "PartyNm" in item
        reg_ab = item.get("RegisteredPartyAb", "").strip()
        has_reg_ab = "RegisteredPartyAb" in item

        named = Party.get_category_named()
        not_named = Party.get_category_not_named()
        not_grouped = Party.get_category_not_grouped()

        if has_reg_ab and reg_ab:
            return named
        elif (has_reg_ab and not reg_ab) and (
            (has_party_ab and party_ab) or (has_party_name and party_name)
        ):
            return not_named
        elif (has_party_ab and not party_ab) or (has_party_name and not party_name):
            return not_grouped
        else:
            return ""

    def _info_candidate_code(self, assembly: Assembly, item: dict):
        first_name = item.get("GivenNm")
        last_name = item.get("Surname")
        electorate_title = self._info_electorate_title(item)
        return self._general.candidate_code(
            assembly.code, electorate_title, first_name, last_name
        )

    def _info_candidate_title(self, item: dict):
        first_name = item.get("GivenNm")
        last_name = item.get("Surname")
        return self._general.candidate_title(first_name, last_name)

    def _info_ballot_code(self, assembly: Assembly, item: dict):
        title = self._info_electorate_title(item)
        return self._general.ballot_code(assembly.code, title)

    # --------------------
    # Methods that know how to create model instance.
    # --------------------

    def _create_notes(self, item: dict):
        state_ab = item.get("StateAb") or item.get("State")
        state_name = item.get("StateNm")
        div_name = item.get("DivisionNm")
        div_id = item.get("DivisionID")

        cat = Note.get_category_raw_info()

        possible = [
            Note(display="state full name", content=state_name, category=cat),
            Note(display="state short name", content=state_ab, category=cat),
            Note(display="division id", content=div_id, category=cat),
            Note(display="division name", content=div_name, category=cat),
        ]
        result = [i for i in possible if i.content]
        return result

    def _create_electorate(self, election: Election, assembly: Assembly, item: dict):
        title = self._info_electorate_title(item)
        code = self._info_electorate_code(assembly, item)
        notes = self._create_notes(item)

        return Electorate(
            code=code,
            title=title,
            ballot_codes=[],
            notes=notes,
            election_code=election.code,
            assembly_code=assembly.code,
            candidate_codes=[],
        )

    def _create_result_electorate_enrolment(
        self, election: Election, assembly: Assembly, item: dict
    ):
        enrolment = int(item.get("Enrolment"))

        # ignore the close of rolls -> adjustments -> enrolment
        # just use the final enrolment figure
        # CloseOfRollsEnrolment
        # NotebookRollAdditions
        # NotebookRollDeletions
        # ReinstatementsPostal
        # ReinstatementsPrePoll
        # ReinstatementsAbsent
        # ReinstatementsProvisional

        pop_code, _ = Result.population_code_title()
        enrol_code, enrol_title = Result.enrolment_code_title()
        part_code, _ = Result.participated_code_title()
        not_part_code, _ = Result.not_participated_code_title()

        title = self._info_electorate_title(item)
        title = f"{title} {enrol_title}"

        code = self._info_result_electorate_code(assembly, item, enrol_code)
        category = Result.category_people_count()
        ancestor_codes = [self._info_result_electorate_code(assembly, item, pop_code)]
        child_codes = [
            self._info_result_electorate_code(assembly, item, not_part_code),
            self._info_result_electorate_code(assembly, item, pop_code),
        ]
        notes = self._create_notes(item)
        electorate_code = self._info_electorate_code(assembly, item)
        ballot_code = self._info_ballot_code(assembly, item)

        return Result(
            code=code,
            title=title,
            value=enrolment,
            category=category,
            ancestor_codes=ancestor_codes,
            child_codes=child_codes,
            notes=notes,
            election_code=election.code,
            assembly_code=assembly.code,
            electorate_code=electorate_code,
            ballot_code=ballot_code,
        )

    def _create_party(self, election: Election, item: dict):
        code = self._info_party_code(election, item)
        short = self._info_party_short(item)
        title = self._info_party_title(item)
        other_name = self._info_party_other_titles(item)
        category = self._info_party_category(item)
        notes = self._create_notes(item)
        return Party(
            code=code,
            short_name=short,
            title=title,
            alt_titles=[i for i in [other_name] if i],
            category=category,
            notes=notes,
            election_code=election.code,
            candidate_codes=[],
        )

    def _create_candidate(self, election: Election, assembly: Assembly, item: dict):
        candidate_last = item.get("Surname")
        candidate_first = item.get("GivenNm")

        code = self._info_candidate_code(assembly, item)
        title = self._info_candidate_title(item)
        notes = self._create_notes(item)
        electorate_code = self._info_electorate_code(assembly, item)
        ballot_code = self._info_ballot_code(assembly, item)
        party_code = self._info_party_code(election, item)
        return Candidate(
            code=code,
            title=title,
            name_first=candidate_first,
            name_last=candidate_last,
            notes=notes,
            election_code=election.code,
            assembly_code=assembly.code,
            electorate_code=electorate_code,
            party_code=party_code,
            ballot_code=ballot_code,
            result_codes=[],
        )

    # --------------------
    # Methods that know the context for creating model instances.
    # --------------------

    def _rows_enrolment_division(
        self, data: list, combination: Combination, election: Election
    ):
        for item in data:
            combination.add(self._create_electorate(election, self._house_reps, item))
            combination.add(
                self._create_result_electorate_enrolment(
                    election, self._house_reps, item
                )
            )

        # 'GeneralEnrolmentByDivisionDownload-24310.csv' = {list: 151} [
        # {'DivisionID': '179', 'DivisionNm': 'Adelaide', 'StateAb': 'SA', 'CloseOfRollsEnrolment': '121614', 'NotebookRollAdditions': '10', 'NotebookRollDeletions': '54', 'ReinstatementsPostal': '1', 'ReinstatementsPrePoll': '4', 'ReinstatementsAbsent': '20', 'ReinstatementsProvisional': '11', 'Enrolment': '121606'},
        # {'DivisionID': '197', 'DivisionNm': 'Aston', 'StateAb': 'VIC', 'CloseOfRollsEnrolment': '110377', 'NotebookRollAdditions': '3', 'NotebookRollDeletions': '41', 'ReinstatementsPostal': '0', 'ReinstatementsPrePoll': '1', 'ReinstatementsAbsent': '2', 'ReinstatementsProvisional': '0', 'Enrolment': '110342'},
        # {'DivisionID': '198', 'DivisionNm': 'Ballarat', 'StateAb': 'VIC', 'CloseOfRollsEnrolment': '114981', 'NotebookRollAdditions': '5', 'NotebookRollDeletions': '36', 'ReinstatementsPostal': '0', 'ReinstatementsPrePoll': '2', 'ReinstatementsAbsent': '1', 'ReinstatementsProvisional': '1', 'Enrolment': '114954'},
        # {'DivisionID': '103', 'DivisionNm': 'Banks', 'StateAb': 'NSW', 'CloseOfRolls...

    def _rows_enrolment_state(
        self, data: list, combination: Combination, election: Election
    ):
        for item in data:
            combination.add(self._create_electorate(election, self._senate, item))
            combination.add(
                self._create_result_electorate_enrolment(election, self._senate, item)
            )

        # 'GeneralEnrolmentByStateDownload-24310.csv' = {list: 8} [
        # {'StateAb': 'NSW', 'StateNm': 'New South Wales', 'CloseOfRollsEnrolment': '5298606', 'NotebookRollAdditions': '79', 'NotebookRollDeletions': '4693', 'ReinstatementsPostal': '13', 'ReinstatementsPrePoll': '142', 'ReinstatementsAbsent': '121', 'ReinstatementsProvisional': '200', 'Enrolment': '5294468'},
        # {'StateAb': 'VIC', 'StateNm': 'Victoria', 'CloseOfRollsEnrolment': '4184955', 'NotebookRollAdditions': '106', 'NotebookRollDeletions': '1271', 'ReinstatementsPostal': '11', 'ReinstatementsPrePoll': '77', 'ReinstatementsAbsent': '105', 'ReinstatementsProvisional': '93', 'Enrolment': '4184076'},
        # {'StateAb': 'QLD', 'StateNm': 'Queensland', 'CloseOfRollsEnrolment': '3262848', 'NotebookRollAdditions': '98', 'NotebookRollDeletions': '887', 'ReinstatementsPostal': '35', 'ReinstatementsPrePoll': '258', 'ReinstatementsAbsent': '217', 'ReinstatementsProvisional': '329', 'Enrolment': '3262898'},
        # {'StateAb': 'WA', 'StateNm': 'Western Australia', 'CloseOfRollsEnrolment': '1645637', 'NotebookRollAddit...

    def _rows_party_details(
        self, data: list, combination: Combination, election: Election
    ):
        for item in data:
            combination.add(self._create_electorate(election, self._senate, item))
            combination.add(self._create_party(election, item))

        # 'GeneralPartyDetailsDownload-24310.csv' = {list: 82} [
        # {'StateAb': 'NSW', 'PartyAb': 'SPP', 'RegisteredPartyAb': 'Sustainable Australia', 'PartyNm': '#Sustainable Australia'},
        # {'StateAb': 'NSW', 'PartyAb': 'AJP', 'RegisteredPartyAb': 'AJP', 'PartyNm': 'Animal Justice Party'},
        # {'StateAb': 'NSW', 'PartyAb': 'AFN', 'RegisteredPartyAb': 'Australia First Party', 'PartyNm': 'Australia First Party (NSW) Incorporated'},
        # {'StateAb': 'NSW', 'PartyAb': 'AAHP', 'RegisteredPartyAb': 'Affordable Housing Party', 'PartyNm': 'Australian Affordable Housing Party'},
        # {'StateAb': 'QLD', 'PartyAb': 'ABFA', 'RegisteredPartyAb': 'ABF', 'PartyNm': 'Australian Better Families'},
        # {'StateAb': 'WA', 'PartyAb': 'AUC', 'RegisteredPartyAb': '', 'PartyNm': 'Australian Christians'},
        # {'StateAb': 'SA', 'PartyAb': 'ACP', 'RegisteredPartyAb': 'Conservatives', 'PartyNm': 'Australian Conservatives'},
        # {'StateAb': 'VIC', 'PartyAb': 'CYA', 'RegisteredPartyAb': '', 'PartyNm': 'Australian Country Party'},
        # {'StateAb': 'SA', 'PartyAb': 'AUD', 'RegisteredPartyAb': '', 'PartyNm': 'Austr...

    def _rows_house_candidates(
        self, data: list, combination: Combination, election: Election
    ):
        for item in data:
            combination.add(self._create_electorate(election, self._house_reps, item))
            combination.add(self._create_party(election, item))
            combination.add(self._create_candidate(election, self._house_reps, item))

        # 'HouseCandidatesDownload-24310.csv' = {list: 1056} [
        # {'StateAb': 'WA', 'DivisionID': '243', 'DivisionNm': "O'Connor", 'PartyAb': 'AUC', 'PartyNm': 'Australian Christians', 'CandidateID': '33328', 'Surname': "'t HART", 'GivenNm': 'Ian', 'Elected': 'N', 'HistoricElected': 'N'},
        # {'StateAb': 'QLD', 'DivisionID': '175', 'DivisionNm': 'Petrie', 'PartyAb': 'ON', 'PartyNm': "Pauline Hanson's One Nation", 'CandidateID': '32556', 'Surname': 'AAI REDDY', 'GivenNm': 'Nikhil', 'Elected': 'N', 'HistoricElected': 'N'},
        # {'StateAb': 'NSW', 'DivisionID': '151', 'DivisionNm': 'Warringah', 'PartyAb': 'LP', 'PartyNm': 'Liberal', 'CandidateID': '33138', 'Surname': 'ABBOTT', 'GivenNm': 'Tony', 'Elected': 'N', 'HistoricElected': 'Y'},
        # {'StateAb': 'NSW', 'DivisionID': '125', 'DivisionNm': 'Hume', 'PartyAb': 'UAPP', 'PartyNm': 'United Australia Party', 'CandidateID': '32774', 'Surname': 'ABDO', 'GivenNm': 'Lynda', 'Elected': 'N', 'HistoricElected': 'N'},
        # {'StateAb': 'NSW', 'DivisionID': '146', 'DivisionNm': 'Robertson', 'PartyAb': 'IND', 'PartyNm': 'Independent'...

    def _rows_house_distribution_preferences(
        self, data: list, combination: Combination, election: Election
    ):

        collect = {
            "state_abb": set(),
            "div_id": set(),
            "div_name": set(),
            "count_number": set(),
            "ballot_position": set(),
            "candidate_id": set(),
            "candidate_last": set(),
            "candidate_first": set(),
            "party_abb": set(),
            "party_name": set(),
            "candidate_elected": set(),
            "calculation_type": set(),
            "calculation_value": set(),
        }
        for item in data:
            collect["state_abb"].add(item.get("StateAb"))
            collect["div_id"].add(item.get("DivisionID"))
            collect["div_name"].add(item.get("DivisionNm"))
            collect["count_number"].add(item.get("CountNumber"))
            collect["ballot_position"].add(item.get("BallotPosition"))
            collect["candidate_id"].add(item.get("CandidateID"))
            collect["candidate_last"].add(item.get("Surname"))
            collect["candidate_first"].add(item.get("GivenNm"))
            collect["party_abb"].add(item.get("PartyAb"))
            collect["party_name"].add(item.get("PartyNm"))
            collect["candidate_elected"].add(
                self._general.get_bool(item.get("Elected"))
            )
            collect["calculation_type"].add(item.get("CalculationType"))
            collect["calculation_value"].add(item.get("CalculationValue"))

        a = 1

        # 'HouseDopByDivisionDownload-24310.csv' = {list: 26632} [
        # {'StateAb': 'ACT', 'DivisionID': '318', 'DivisionNm': 'Bean', 'CountNumber': '0', 'BallotPosition': '1', 'CandidateID': '33426', 'Surname': 'FAULKNER', 'GivenNm': 'Therese', 'PartyAb': 'AUP', 'PartyNm': 'Australian Progressives', 'Elected': 'N', 'HistoricElected': 'N', 'CalculationType': 'Preference Count', 'CalculationValue': '2722'},
        # {'StateAb': 'ACT', 'DivisionID': '318', 'DivisionNm': 'Bean', 'CountNumber': '0', 'BallotPosition': '1', 'CandidateID': '33426', 'Surname': 'FAULKNER', 'GivenNm': 'Therese', 'PartyAb': 'AUP', 'PartyNm': 'Australian Progressives', 'Elected': 'N', 'HistoricElected': 'N', 'CalculationType': 'Preference Percent', 'CalculationValue': '2.93'},
        # {'StateAb': 'ACT', 'DivisionID': '318', 'DivisionNm': 'Bean', 'CountNumber': '0', 'BallotPosition': '1', 'CandidateID': '33426', 'Surname': 'FAULKNER', 'GivenNm': 'Therese', 'PartyAb': 'AUP', 'PartyNm': 'Australian Progressives', 'Elected': 'N', 'HistoricElected': 'N', 'CalculationType': 'Transfer Count', 'CalculationVa...

        pass

    def _rows_house_informal_division(
        self, data: list, combination: Combination, election: Election
    ):
        # 'HouseInformalByDivisionDownload-24310.csv' = {list: 151} [
        # {'DivisionID': '107', 'DivisionNm': 'Blaxland', 'StateAb': 'NSW', 'FormalVotes': '80808', 'InformalVotes': '12401', 'TotalVotes': '93209', 'InformalPercent': '13.3', 'InformalSwing': '1.75'},
        # {'DivisionID': '119', 'DivisionNm': 'Fowler', 'StateAb': 'NSW', 'FormalVotes': '83664', 'InformalVotes': '12624', 'TotalVotes': '96288', 'InformalPercent': '13.11', 'InformalSwing': '2.7'},
        # {'DivisionID': '251', 'DivisionNm': 'Watson', 'StateAb': 'NSW', 'FormalVotes': '84250', 'InformalVotes': '12159', 'TotalVotes': '96409', 'InformalPercent': '12.61', 'InformalSwing': '1.96'},
        # {'DivisionID': '315', 'DivisionNm': 'McMahon', 'StateAb': 'NSW', 'FormalVotes': '85393', 'InformalVotes': '11731', 'TotalVotes': '97124', 'InformalPercent': '12.08', 'InformalSwing': '2.19'},
        # {'DivisionID': '153', 'DivisionNm': 'Werriwa', 'StateAb': 'NSW', 'FormalVotes': '94229', 'InformalVotes': '12324', 'TotalVotes': '106553', 'InformalPercent': '11.57', 'InformalSwing': '2.81'},
        # {'DivisionID': '224', 'DivisionNm': 'Mall...

        pass

    def _rows_house_informal_state(
        self, data: list, combination: Combination, election: Election
    ):
        # 'HouseInformalByStateDownload-24310.csv' = {list: 8} [
        # {'StateAb': 'NSW', 'StateNm': 'New South Wales', 'FormalVotes': '4537336', 'InformalVotes': '342051', 'TotalVotes': '4879387', 'InformalPercent': '7.01', 'InformalSwing': '0.84'},
        # {'StateAb': 'VIC', 'StateNm': 'Victoria', 'FormalVotes': '3695032', 'InformalVotes': '180426', 'TotalVotes': '3875458', 'InformalPercent': '4.66', 'InformalSwing': '-0.11'},
        # {'StateAb': 'QLD', 'StateNm': 'Queensland', 'FormalVotes': '2829018', 'InformalVotes': '147290', 'TotalVotes': '2976308', 'InformalPercent': '4.95', 'InformalSwing': '0.25'},
        # {'StateAb': 'WA', 'StateNm': 'Western Australia', 'FormalVotes': '1401874', 'InformalVotes': '80575', 'TotalVotes': '1482449', 'InformalPercent': '5.44', 'InformalSwing': '1.45'},
        # {'StateAb': 'SA', 'StateNm': 'South Australia', 'FormalVotes': '1072648', 'InformalVotes': '54202', 'TotalVotes': '1126850', 'InformalPercent': '4.81', 'InformalSwing': '0.63'},
        # {'StateAb': 'TAS', 'StateNm': 'Tasmania', 'FormalVotes': '347992', 'InformalVotes': '15970', 'TotalVotes': '3639...

        pass

    def _rows_house_turnout_division(
        self, data: list, combination: Combination, election: Election
    ):
        # 'HouseTurnoutByDivisionDownload-24310.csv' = {list: 151} [
        # {'DivisionID': '179', 'DivisionNm': 'Adelaide', 'StateAb': 'SA', 'Enrolment': '121606', 'Turnout': '111299', 'TurnoutPercentage': '91.52', 'TurnoutSwing': '1.73'},
        # {'DivisionID': '197', 'DivisionNm': 'Aston', 'StateAb': 'VIC', 'Enrolment': '110342', 'Turnout': '103919', 'TurnoutPercentage': '94.18', 'TurnoutSwing': '-0.69'},
        # {'DivisionID': '198', 'DivisionNm': 'Ballarat', 'StateAb': 'VIC', 'Enrolment': '114954', 'Turnout': '107372', 'TurnoutPercentage': '93.4', 'TurnoutSwing': '1.03'},
        # {'DivisionID': '103', 'DivisionNm': 'Banks', 'StateAb': 'NSW', 'Enrolment': '106253', 'Turnout': '98845', 'TurnoutPercentage': '93.03', 'TurnoutSwing': '1.04'},
        # {'DivisionID': '180', 'DivisionNm': 'Barker', 'StateAb': 'SA', 'Enrolment': '118371', 'Turnout': '111893', 'TurnoutPercentage': '94.53', 'TurnoutSwing': '0.5'},
        # {'DivisionID': '104', 'DivisionNm': 'Barton', 'StateAb': 'NSW', 'Enrolment': '108992', 'Turnout': '99380', 'TurnoutPercentage': '91.18', 'TurnoutSwing': '1.34'},
        # {'DivisionID': '192', 'D...

        pass

    def _rows_house_turnout_state(
        self, data: list, combination: Combination, election: Election
    ):
        # 'HouseTurnoutByStateDownload-24310.csv' = {list: 8} [
        # {'StateAb': 'NSW', 'StateNm': 'New South Wales', 'Enrolment': '5294468', 'Turnout': '4879387', 'TurnoutPercentage': '92.16', 'TurnoutSwing': '0.67'},
        # {'StateAb': 'VIC', 'StateNm': 'Victoria', 'Enrolment': '4184076', 'Turnout': '3875458', 'TurnoutPercentage': '92.62', 'TurnoutSwing': '1.48'},
        # {'StateAb': 'QLD', 'StateNm': 'Queensland', 'Enrolment': '3262898', 'Turnout': '2976308', 'TurnoutPercentage': '91.22', 'TurnoutSwing': '0.05'},
        # {'StateAb': 'WA', 'StateNm': 'Western Australia', 'Enrolment': '1646262', 'Turnout': '1482449', 'TurnoutPercentage': '90.05', 'TurnoutSwing': '1.67'},
        # {'StateAb': 'SA', 'StateNm': 'South Australia', 'Enrolment': '1210817', 'Turnout': '1126850', 'TurnoutPercentage': '93.07', 'TurnoutSwing': '1.26'},
        # {'StateAb': 'TAS', 'StateNm': 'Tasmania', 'Enrolment': '385816', 'Turnout': '363962', 'TurnoutPercentage': '94.34', 'TurnoutSwing': '0.75'},
        # {'StateAb': 'ACT', 'StateNm': 'Australian Capital Territory', 'Enrolment': '295847', 'Turnout': '275591', 'TurnoutPercen...

        pass

    def _rows_house_votes_division(
        self, data: list, combination: Combination, election: Election
    ):
        # 'HouseVotesCountedByDivisionDownload-24310.csv' = {list: 151} [
        # {'DivisionID': '179', 'DivisionNm': 'Adelaide', 'StateAb': 'SA', 'Enrolment': '121606', 'OrdinaryVotes': '85576', 'AbsentVotes': '7443', 'ProvisionalVotes': '769', 'PrePollVotes': '5443', 'PostalVotes': '12068', 'TotalVotes': '111299', 'TotalPercentage': '91.52'},
        # {'DivisionID': '197', 'DivisionNm': 'Aston', 'StateAb': 'VIC', 'Enrolment': '110342', 'OrdinaryVotes': '87126', 'AbsentVotes': '3821', 'ProvisionalVotes': '180', 'PrePollVotes': '3897', 'PostalVotes': '8895', 'TotalVotes': '103919', 'TotalPercentage': '94.18'},
        # {'DivisionID': '198', 'DivisionNm': 'Ballarat', 'StateAb': 'VIC', 'Enrolment': '114954', 'OrdinaryVotes': '90662', 'AbsentVotes': '3302', 'ProvisionalVotes': '238', 'PrePollVotes': '3352', 'PostalVotes': '9818', 'TotalVotes': '107372', 'TotalPercentage': '93.4'},
        # {'DivisionID': '103', 'DivisionNm': 'Banks', 'StateAb': 'NSW', 'Enrolment': '106253', 'OrdinaryVotes': '83406', 'AbsentVotes': '4067', 'ProvisionalVotes': '272', 'PrePollVotes': '4334', 'PostalVotes': '6766',...

        pass

    def _rows_house_votes_state(
        self, data: list, combination: Combination, election: Election
    ):
        # 'HouseVotesCountedByStateDownload-24310.csv' = {list: 8} [
        # {'StateAb': 'NSW', 'StateNm': 'New South Wales', 'Enrolment': '5294468', 'OrdinaryVotes': '4206944', 'AbsentVotes': '194182', 'ProvisionalVotes': '14490', 'PrePollVotes': '185304', 'PostalVotes': '278467', 'TotalVotes': '4879387', 'TotalPercentage': '92.16'},
        # {'StateAb': 'VIC', 'StateNm': 'Victoria', 'Enrolment': '4184076', 'OrdinaryVotes': '3135885', 'AbsentVotes': '161828', 'ProvisionalVotes': '11149', 'PrePollVotes': '184014', 'PostalVotes': '382582', 'TotalVotes': '3875458', 'TotalPercentage': '92.62'},
        # {'StateAb': 'QLD', 'StateNm': 'Queensland', 'Enrolment': '3262898', 'OrdinaryVotes': '2432981', 'AbsentVotes': '108349', 'ProvisionalVotes': '8978', 'PrePollVotes': '117343', 'PostalVotes': '308657', 'TotalVotes': '2976308', 'TotalPercentage': '91.22'},
        # {'StateAb': 'WA', 'StateNm': 'Western Australia', 'Enrolment': '1646262', 'OrdinaryVotes': '1195932', 'AbsentVotes': '81012', 'ProvisionalVotes': '7341', 'PrePollVotes': '72931', 'PostalVotes': '125233', 'TotalVotes': '1482449', 'To...

        pass

    def _rows_senate_candidates(
        self, data: list, combination: Combination, election: Election
    ):
        # 'SenateCandidatesDownload-24310.csv' = {list: 458} [
        # {'StateAb': 'QLD', 'PartyAb': 'FACN', 'PartyNm': "FRASER ANNING'S CONSERVATIVE NATIONAL PARTY", 'CandidateID': '33613', 'Surname': 'ABSOLON', 'GivenNm': 'Mark', 'Elected': 'N', 'HistoricElected': 'N'},
        # {'StateAb': 'SA', 'PartyAb': 'HMP', 'PartyNm': 'Help End Marijuana Prohibition (HEMP) Party', 'CandidateID': '33096', 'Surname': 'ADAMS', 'GivenNm': 'Angela', 'Elected': 'N', 'HistoricElected': 'N'},
        # {'StateAb': 'SA', 'PartyAb': 'GAP', 'PartyNm': 'The Great Australian Party', 'CandidateID': '33465', 'Surname': 'ALDRIDGE', 'GivenNm': 'Mark', 'Elected': 'N', 'HistoricElected': 'N'},
        # {'StateAb': 'SA', 'PartyAb': 'CEC', 'PartyNm': 'Citizens Electoral Council', 'CandidateID': '32502', 'Surname': 'ALLWOOD', 'GivenNm': 'Sean', 'Elected': 'N', 'HistoricElected': 'N'},
        # {'StateAb': 'ACT', 'PartyAb': 'SPP', 'PartyNm': 'Sustainable Australia', 'CandidateID': '32256', 'Surname': 'ANGEL', 'GivenNm': 'Joy', 'Elected': 'N', 'HistoricElected': 'N'},
        # {'StateAb': 'QLD', 'PartyAb': 'FACN', 'PartyNm': "FRAS...

        pass

    def _rows_senate_informal_division(
        self, data: list, combination: Combination, election: Election
    ):
        # 'SenateInformalByDivisionDownload-24310.csv' = {list: 151} [
        # {'DivisionID': '107', 'DivisionNm': 'Blaxland', 'StateAb': 'NSW', 'FormalVotes': '85410', 'InformalVotes': '8312', 'TotalVotes': '93722', 'InformalPercent': '8.87'},
        # {'DivisionID': '119', 'DivisionNm': 'Fowler', 'StateAb': 'NSW', 'FormalVotes': '90309', 'InformalVotes': '7388', 'TotalVotes': '97697', 'InformalPercent': '7.56'},
        # {'DivisionID': '251', 'DivisionNm': 'Watson', 'StateAb': 'NSW', 'FormalVotes': '90431', 'InformalVotes': '7255', 'TotalVotes': '97686', 'InformalPercent': '7.43'},
        # {'DivisionID': '315', 'DivisionNm': 'McMahon', 'StateAb': 'NSW', 'FormalVotes': '91044', 'InformalVotes': '6996', 'TotalVotes': '98040', 'InformalPercent': '7.14'},
        # {'DivisionID': '153', 'DivisionNm': 'Werriwa', 'StateAb': 'NSW', 'FormalVotes': '99472', 'InformalVotes': '7430', 'TotalVotes': '106902', 'InformalPercent': '6.95'},
        # {'DivisionID': '203', 'DivisionNm': 'Calwell', 'StateAb': 'VIC', 'FormalVotes': '90060', 'InformalVotes': '6484', 'TotalVotes': '96544', 'InformalPercent': '6.72'},
        # {'Divisio...

        pass

    def _rows_senate_informal_state(
        self, data: list, combination: Combination, election: Election
    ):
        # 'SenateInformalByStateDownload-24310.csv' = {list: 8} [
        # {'StateAb': 'NSW', 'StateNm': 'New South Wales', 'FormalVotes': '4695326', 'InformalVotes': '210146', 'TotalVotes': '4905472', 'InformalPercent': '4.28', 'InformalSwing': '-0.25'},
        # {'StateAb': 'VIC', 'StateNm': 'Victoria', 'FormalVotes': '3739443', 'InformalVotes': '156793', 'TotalVotes': '3896236', 'InformalPercent': '4.02', 'InformalSwing': '-0.18'},
        # {'StateAb': 'QLD', 'StateNm': 'Queensland', 'FormalVotes': '2901464', 'InformalVotes': '97908', 'TotalVotes': '2999372', 'InformalPercent': '3.26', 'InformalSwing': '-0.14'},
        # {'StateAb': 'WA', 'StateNm': 'Western Australia', 'FormalVotes': '1446623', 'InformalVotes': '50909', 'TotalVotes': '1497532', 'InformalPercent': '3.4', 'InformalSwing': '0.05'},
        # {'StateAb': 'SA', 'StateNm': 'South Australia', 'FormalVotes': '1094823', 'InformalVotes': '39733', 'TotalVotes': '1134556', 'InformalPercent': '3.5', 'InformalSwing': '0.17'},
        # {'StateAb': 'TAS', 'StateNm': 'Tasmania', 'FormalVotes': '351988', 'InformalVotes': '13284', 'TotalVotes': '36527...

        pass

    def _rows_senate_distribution_preferences(
        self, data: list, combination: Combination, election: Election
    ):
        collect = {
            "state": set(),
            "vacancies": set(),
            "total_formal_papers": set(),
            "quota": set(),
            "count": set(),
            "ballot_position": set(),
            "ticket": set(),
            "candidate_last": set(),
            "candidate_first": set(),
            "papers": set(),
            "vote_transferred": set(),
            "progressive_vote_total": set(),
            "transfer_value": set(),
            "status": set(),
            "changed": set(),
            "order_elected": set(),
            "comment": set(),
        }
        for item in data:
            collect["state"].add(item.get("State"))
            collect["vacancies"].add(item.get("No Of Vacancies"))
            collect["total_formal_papers"].add(item.get("Total Formal Papers"))
            collect["quota"].add(item.get("Quota"))
            collect["count"].add(item.get("Count"))
            collect["ballot_position"].add(item.get("Ballot Position"))
            collect["ticket"].add(item.get("Ticket"))
            collect["candidate_last"].add(item.get("Surname"))
            collect["candidate_first"].add(item.get("GivenNm"))
            collect["papers"].add(item.get("Papers"))
            collect["vote_transferred"].add(item.get("VoteTransferred"))
            collect["progressive_vote_total"].add(item.get("ProgressiveVoteTotal"))
            collect["transfer_value"].add(item.get("Transfer Value"))
            collect["status"].add(item.get("Status"))
            collect["changed"].add(item.get("Changed"))
            collect["order_elected"].add(item.get("Order Elected"))
            collect["comment"].add(item.get("Comment"))

        a = 1
        # 'SenateStateDOPDownload-24310-ACT.csv' = {list: 475} [
        # {'State': 'ACT', 'No Of Vacancies': '2', 'Total Formal Papers': '270231', 'Quota': '90078', 'Count': '1', 'Ballot Position': '8', 'Ticket': ' A', 'Surname': 'SESELJA', 'GivenNm': 'Zed', 'Papers': '84603', 'VoteTransferred': '84603', 'ProgressiveVoteTotal': '84603', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'GALLAGHER ,K has 14856 surplus vote(s) to be distributed in count # 2 at a transfer value of 0.141574704099719. 104934 papers are involved from count number(s) 1.'},
        # {'State': 'ACT', 'No Of Vacancies': '2', 'Total Formal Papers': '270231', 'Quota': '90078', 'Count': '1', 'Ballot Position': '9', 'Ticket': ' A', 'Surname': 'GUNNING', 'GivenNm': 'Robert', 'Papers': '2889', 'VoteTransferred': '2889', 'ProgressiveVoteTotal': '2889', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'GALLAGHER ,K has 14856 surplus vote(s) to be distributed in count # 2 at ...
        # 'SenateStateDOPDownload-24310-NSW.csv' = {list: 45903} [
        # {'State': 'NSW', 'No Of Vacancies': '6', 'Total Formal Papers': '4695326', 'Quota': '670761', 'Count': '1', 'Ballot Position': '36', 'Ticket': ' A', 'Surname': 'NICHOLS', 'GivenNm': 'Maree', 'Papers': '32778', 'VoteTransferred': '32778', 'ProgressiveVoteTotal': '32778', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'HUGHES ,H has 993427 surplus vote(s) to be distributed in count # 2 at a transfer value of 0.596943975079738. 1664188 papers are involved from count number(s) 1.'},
        # {'State': 'NSW', 'No Of Vacancies': '6', 'Total Formal Papers': '4695326', 'Quota': '670761', 'Count': '1', 'Ballot Position': '37', 'Ticket': ' A', 'Surname': 'SHIGROV', 'GivenNm': 'Vladimir', 'Papers': '366', 'VoteTransferred': '366', 'ProgressiveVoteTotal': '366', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'HUGHES ,H has 993427 surplus vote(s) to be distributed in count # 2...
        # 'SenateStateDOPDownload-24310-NT.csv' = {list: 20} [
        # {'State': 'NT', 'No Of Vacancies': '2', 'Total Formal Papers': '105027', 'Quota': '35010', 'Count': '1', 'Ballot Position': '10', 'Ticket': ' A', 'Surname': 'WOLF', 'GivenNm': 'Michael J', 'Papers': '6380', 'VoteTransferred': '6380', 'ProgressiveVoteTotal': '6380', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'McCARTHY, M, McMAHON, S have been elected to the remaining positions.'},
        # {'State': 'NT', 'No Of Vacancies': '2', 'Total Formal Papers': '105027', 'Quota': '35010', 'Count': '1', 'Ballot Position': '11', 'Ticket': ' A', 'Surname': 'McROBERT', 'GivenNm': 'Ross Thomas', 'Papers': '89', 'VoteTransferred': '89', 'ProgressiveVoteTotal': '89', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'McCARTHY, M, McMAHON, S have been elected to the remaining positions.'},
        # {'State': 'NT', 'No Of Vacancies': '2', 'Total Formal Papers': '105027', 'Quota': '35010', 'C...
        # 'SenateStateDOPDownload-24310-QLD.csv' = {list: 24480} [
        # {'State': 'QLD', 'No Of Vacancies': '6', 'Total Formal Papers': '2901464', 'Quota': '414495', 'Count': '1', 'Ballot Position': '27', 'Ticket': ' A', 'Surname': 'HEALY', 'GivenNm': 'Graham', 'Papers': '22207', 'VoteTransferred': '22207', 'ProgressiveVoteTotal': '22207', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'SCARR ,P has 693611 surplus vote(s) to be distributed in count # 2 at a transfer value of 0.625942824964398. 1108106 papers are involved from count number(s) 1.'},
        # {'State': 'QLD', 'No Of Vacancies': '6', 'Total Formal Papers': '2901464', 'Quota': '414495', 'Count': '1', 'Ballot Position': '28', 'Ticket': ' A', 'Surname': 'HENAWAY', 'GivenNm': 'Lionel', 'Papers': '322', 'VoteTransferred': '322', 'ProgressiveVoteTotal': '322', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'SCARR ,P has 693611 surplus vote(s) to be distributed in count # 2 at a...
        # 'SenateStateDOPDownload-24310-SA.csv' = {list: 7788} [
        # {'State': 'SA', 'No Of Vacancies': '6', 'Total Formal Papers': '1094823', 'Quota': '156404', 'Count': '1', 'Ballot Position': '17', 'Ticket': ' A', 'Surname': 'ALDRIDGE', 'GivenNm': 'Mark', 'Papers': '12426', 'VoteTransferred': '12426', 'ProgressiveVoteTotal': '12426', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'RUSTON ,A has 252056 surplus vote(s) to be distributed in count # 2 at a transfer value of 0.617088576604808. 408460 papers are involved from count number(s) 1.'},
        # {'State': 'SA', 'No Of Vacancies': '6', 'Total Formal Papers': '1094823', 'Quota': '156404', 'Count': '1', 'Ballot Position': '18', 'Ticket': ' A', 'Surname': 'MATTHEWS', 'GivenNm': 'Gary', 'Papers': '272', 'VoteTransferred': '272', 'ProgressiveVoteTotal': '272', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'RUSTON ,A has 252056 surplus vote(s) to be distributed in count # 2 at a ...
        # 'SenateStateDOPDownload-24310-TAS.csv' = {list: 6394} [
        # {'State': 'TAS', 'No Of Vacancies': '6', 'Total Formal Papers': '351988', 'Quota': '50285', 'Count': '1', 'Ballot Position': '17', 'Ticket': ' A', 'Surname': 'STRINGER', 'GivenNm': 'Justin', 'Papers': '3695', 'VoteTransferred': '3695', 'ProgressiveVoteTotal': '3695', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'COLBECK ,R has 56292 surplus vote(s) to be distributed in count # 2 at a transfer value of 0.528181502575602. 106577 papers are involved from count number(s) 1.'},
        # {'State': 'TAS', 'No Of Vacancies': '6', 'Total Formal Papers': '351988', 'Quota': '50285', 'Count': '1', 'Ballot Position': '18', 'Ticket': ' A', 'Surname': 'FRAME', 'GivenNm': 'Nigel', 'Papers': '127', 'VoteTransferred': '127', 'ProgressiveVoteTotal': '127', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'COLBECK ,R has 56292 surplus vote(s) to be distributed in count # 2 at a trans...
        # 'SenateStateDOPDownload-24310-VIC.csv' = {list: 30828} [
        # {'State': 'VIC', 'No Of Vacancies': '6', 'Total Formal Papers': '3739443', 'Quota': '534207', 'Count': '1', 'Ballot Position': '32', 'Ticket': ' A', 'Surname': 'PATERSON', 'GivenNm': 'James', 'Papers': '1332146', 'VoteTransferred': '1332146', 'ProgressiveVoteTotal': '1332146', 'Transfer Value': '1.000000000000000000000000000', 'Status': 'Elected', 'Changed': 'True', 'Order Elected': '1', 'Comment': 'PATERSON ,J has 797939 surplus vote(s) to be distributed in count # 2 at a transfer value of 0.598987648500990. 1332146 papers are involved from count number(s) 1.'},
        # {'State': 'VIC', 'No Of Vacancies': '6', 'Total Formal Papers': '3739443', 'Quota': '534207', 'Count': '1', 'Ballot Position': '33', 'Ticket': ' A', 'Surname': 'HUME', 'GivenNm': 'Jane', 'Papers': '4217', 'VoteTransferred': '4217', 'ProgressiveVoteTotal': '4217', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'PATERSON ,J has 797939 surplus vote(s) to be distri...
        # 'SenateStateDOPDownload-24310-WA.csv' = {list: 15939} [
        # {'State': 'WA', 'No Of Vacancies': '6', 'Total Formal Papers': '1446623', 'Quota': '206661', 'Count': '1', 'Ballot Position': '24', 'Ticket': ' A', 'Surname': 'GEORGIOU', 'GivenNm': 'Peter', 'Papers': '84677', 'VoteTransferred': '84677', 'ProgressiveVoteTotal': '84677', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'REYNOLDS ,L has 381960 surplus vote(s) to be distributed in count # 2 at a transfer value of 0.648906512000081. 588621 papers are involved from count number(s) 1.'},
        # {'State': 'WA', 'No Of Vacancies': '6', 'Total Formal Papers': '1446623', 'Quota': '206661', 'Count': '1', 'Ballot Position': '25', 'Ticket': ' A', 'Surname': 'SUTER', 'GivenNm': 'Martin Graham', 'Papers': '452', 'VoteTransferred': '452', 'ProgressiveVoteTotal': '452', 'Transfer Value': '1.000000000000000000000000000', 'Status': '', 'Changed': '', 'Order Elected': '0', 'Comment': 'REYNOLDS ,L has 381960 surplus vote(s) to be distributed in coun...

        pass

    def _rows_senate_turnout_division(
        self, data: list, combination: Combination, election: Election
    ):
        # 'SenateTurnoutByDivisionDownload-24310.csv' = {list: 151} [
        # {'DivisionID': '179', 'DivisionNm': 'Adelaide', 'StateAb': 'SA', 'Enrolment': '121606', 'Turnout': '112647', 'TurnoutPercentage': '92.63'},
        # {'DivisionID': '197', 'DivisionNm': 'Aston', 'StateAb': 'VIC', 'Enrolment': '110342', 'Turnout': '104345', 'TurnoutPercentage': '94.57'},
        # {'DivisionID': '198', 'DivisionNm': 'Ballarat', 'StateAb': 'VIC', 'Enrolment': '114954', 'Turnout': '107526', 'TurnoutPercentage': '93.54'},
        # {'DivisionID': '103', 'DivisionNm': 'Banks', 'StateAb': 'NSW', 'Enrolment': '106253', 'Turnout': '99684', 'TurnoutPercentage': '93.82'},
        # {'DivisionID': '180', 'DivisionNm': 'Barker', 'StateAb': 'SA', 'Enrolment': '118371', 'Turnout': '112547', 'TurnoutPercentage': '95.08'},
        # {'DivisionID': '104', 'DivisionNm': 'Barton', 'StateAb': 'NSW', 'Enrolment': '108992', 'Turnout': '99573', 'TurnoutPercentage': '91.36'},
        # {'DivisionID': '192', 'DivisionNm': 'Bass', 'StateAb': 'TAS', 'Enrolment': '76532', 'Turnout': '72288', 'TurnoutPercentage': '94.45'},
        # {'DivisionID': '318', 'DivisionN...

        pass

    def _rows_senate_votes_division(
        self, data: list, combination: Combination, election: Election
    ):
        # 'SenateVotesCountedByDivisionDownload-24310.csv' = {list: 151} [
        # {'DivisionID': '179', 'DivisionNm': 'Adelaide', 'StateAb': 'SA', 'Enrolment': '121606', 'OrdinaryVotes': '85915', 'AbsentVotes': '7913', 'ProvisionalVotes': '1292', 'PrePollVotes': '5480', 'PostalVotes': '12047', 'TotalVotes': '112647', 'TotalPercentage': '92.63'},
        # {'DivisionID': '197', 'DivisionNm': 'Aston', 'StateAb': 'VIC', 'Enrolment': '110342', 'OrdinaryVotes': '87069', 'AbsentVotes': '4060', 'ProvisionalVotes': '420', 'PrePollVotes': '3918', 'PostalVotes': '8878', 'TotalVotes': '104345', 'TotalPercentage': '94.57'},
        # {'DivisionID': '198', 'DivisionNm': 'Ballarat', 'StateAb': 'VIC', 'Enrolment': '114954', 'OrdinaryVotes': '90468', 'AbsentVotes': '3485', 'ProvisionalVotes': '408', 'PrePollVotes': '3380', 'PostalVotes': '9785', 'TotalVotes': '107526', 'TotalPercentage': '93.54'},
        # {'DivisionID': '103', 'DivisionNm': 'Banks', 'StateAb': 'NSW', 'Enrolment': '106253', 'OrdinaryVotes': '83611', 'AbsentVotes': '4317', 'ProvisionalVotes': '640', 'PrePollVotes': '4360', 'PostalVotes': '6756...

        pass

    def _rows_senate_votes_state(
        self, data: list, combination: Combination, election: Election
    ):
        # 'SenateVotesCountedByStateDownload-24310.csv' = {list: 8} [
        # {'StateAb': 'NSW', 'StateNm': 'New South Wales', 'Enrolment': '5294468', 'OrdinaryVotes': '4209014', 'AbsentVotes': '204332', 'ProvisionalVotes': '27717', 'PrePollVotes': '186496', 'PostalVotes': '277913', 'TotalVotes': '4905472', 'TotalPercentage': '92.65'},
        # {'StateAb': 'VIC', 'StateNm': 'Victoria', 'Enrolment': '4184076', 'OrdinaryVotes': '3136433', 'AbsentVotes': '171484', 'ProvisionalVotes': '21761', 'PrePollVotes': '185219', 'PostalVotes': '381339', 'TotalVotes': '3896236', 'TotalPercentage': '93.12'},
        # {'StateAb': 'QLD', 'StateNm': 'Queensland', 'Enrolment': '3262898', 'OrdinaryVotes': '2433629', 'AbsentVotes': '119700', 'ProvisionalVotes': '21031', 'PrePollVotes': '118114', 'PostalVotes': '306898', 'TotalVotes': '2999372', 'TotalPercentage': '91.92'},
        # {'StateAb': 'WA', 'StateNm': 'Western Australia', 'Enrolment': '1646262', 'OrdinaryVotes': '1196330', 'AbsentVotes': '88960', 'ProvisionalVotes': '14383', 'PrePollVotes': '73316', 'PostalVotes': '124543', 'TotalVotes': '1497532', '...

        pass


# AbsentVotes
# BallotPosition
# CalculationType
# CalculationValue
# CandidateID
# Changed
# CloseOfRollsEnrolment
# Comment
# Count
# CountNumber
# DivisionID
# DivisionNm
# Elected
# Enrolment
# FormalVotes
# GivenNm
# HistoricElected
# InformalPercent
# InformalSwing
# InformalVotes
# NotebookRollAdditions
# NotebookRollDeletions
# OrdinaryVotes
# Papers
# PartyAb
# PartyNm
# Position
# PostalVotes
# PrePollVotes
# ProgressiveVoteTotal
# ProvisionalVotes
# Quota
# RegisteredPartyAb
# ReinstatementsAbsent
# ReinstatementsPostal
# ReinstatementsPrePoll
# ReinstatementsProvisional
# State
# StateAb
# StateNm
# Status
# Surname
# Ticket
# TotalPercentage
# TotalVotes
# Turnout
# TurnoutPercentage
# TurnoutSwing
# Vacancies
# Value
# VoteTransferred

# absentvotes = item.get("AbsentVotes")
# ballotposition = item.get("BallotPosition")
# calculationtype = item.get("CalculationType")
# calculationvalue = item.get("CalculationValue")
# changed = item.get("Changed")
# closeofrollsenrolment = item.get("CloseOfRollsEnrolment")
# comment = item.get("Comment")
# count = item.get("Count")
# countnumber = item.get("CountNumber")
# elected = item.get("Elected")
# enrolment = item.get("Enrolment")
# formalvotes = item.get("FormalVotes")
# historicelected = item.get("HistoricElected")
# informalpercent = item.get("InformalPercent")
# informalswing = item.get("InformalSwing")
# informalvotes = item.get("InformalVotes")
# notebookrolladditions = item.get("NotebookRollAdditions")
# notebookrolldeletions = item.get("NotebookRollDeletions")
# ordinaryvotes = item.get("OrdinaryVotes")
# papers = item.get("Papers")
# position = item.get("Position")
# postalvotes = item.get("PostalVotes")
# prepollvotes = item.get("PrePollVotes")
# progressivevotetotal = item.get("ProgressiveVoteTotal")
# provisionalvotes = item.get("ProvisionalVotes")
# quota = item.get("Quota")
#
# reinstatementsabsent = item.get("ReinstatementsAbsent")
# reinstatementspostal = item.get("ReinstatementsPostal")
# reinstatementsprepoll = item.get("ReinstatementsPrePoll")
# reinstatementsprovisional = item.get("ReinstatementsProvisional")
# status = item.get("Status")
# ticket = item.get("Ticket")
# totalpercentage = item.get("TotalPercentage")
# totalvotes = item.get("TotalVotes")
# turnout = item.get("Turnout")
# turnoutpercentage = item.get("TurnoutPercentage")
# turnoutswing = item.get("TurnoutSwing")
# vacancies = item.get("Vacancies")
# value = item.get("Value")
# votetransferred = item.get("VoteTransferred")
