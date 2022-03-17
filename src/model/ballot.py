from dataclasses import dataclass
from typing import Collection

from dataclasses_json import dataclass_json, LetterCase

from src.helper.general import General
from src.model.note import Note


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Ballot:
    code: str
    category: str
    """The category of ballot. One of: 'party' or 'candidate'."""

    group_candidates_by_party: bool
    """Whether to group candidates by party.
    Only relevant when showing candidates."""

    order_method: str
    """The ordering method.
    One of: 'fixed', 'robson-rotation'.
    This specifies if the order of the items in orderCodes matters or not."""

    notes: list[Note]

    election_code: str
    assembly_code: str
    electorate_code: str
    party_codes: list[str]
    """The party codes on this ballot.
    They might be in order depending on orderMethod."""

    candidate_codes: list[str]
    """The candidate codes on this ballot.
    They might be in order depending on orderMethod."""

    result_codes: list[str]
    """The ballot results."""

    @classmethod
    def get_category_candidate(cls):
        return "candidate"

    @classmethod
    def get_order_fixed(cls):
        return "fixed"

    def merge_in(self, other: "Ballot") -> None:
        General.pick_match_not_empty(self.code, other.code)
        General.pick_match_not_empty(self.category, other.category)
        General.pick_match_not_empty(
            self.group_candidates_by_party, other.group_candidates_by_party
        )
        General.pick_match_not_empty(self.order_method, other.order_method)
        General.pick_match_not_empty(self.election_code, other.election_code)
        General.pick_match_not_empty(self.assembly_code, other.assembly_code)
        General.pick_match_not_empty(self.electorate_code, other.electorate_code)

        candidate_codes = self.candidate_codes + other.candidate_codes
        party_codes = self.party_codes + other.party_codes
        result_codes = self.result_codes + other.result_codes
        notes = self.notes + other.notes

        self.candidate_codes = General.merge_list_str(candidate_codes)
        self.party_codes = General.merge_list_str(party_codes)
        self.result_codes = General.merge_list_str(result_codes)
        self.notes = Note.normalise(notes)

    def add_to(self, collection: list["Ballot"]) -> None:
        existing = self.find_in(collection, self)
        if existing:
            existing.merge_in(self)
        else:
            collection.append(self)

    @classmethod
    def normalise(cls, collection: list["Ballot"]) -> list["Ballot"]:
        result = []
        for item in sorted(collection, key=lambda x: x.code):
            item.add_to(result)
        return result

    @classmethod
    def find_in(cls, collection: Collection["Ballot"], item: "Ballot") -> "Ballot":
        result = next((i for i in collection if i.code == item.code), None)
        return result
