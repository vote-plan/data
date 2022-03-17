from dataclasses import dataclass
from typing import Collection

from dataclasses_json import dataclass_json, LetterCase

from src.helper.general import General
from src.model.note import Note


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Candidate:
    code: str
    title: str
    name_first: str
    name_last: str
    notes: list[Note]

    election_code: str
    assembly_code: str
    electorate_code: str
    party_code: str
    ballot_code: str
    result_codes: list[str]

    def merge_in(self, other: "Candidate") -> None:
        General.pick_match_not_empty(self.code, other.code)
        General.pick_match_not_empty(self.name_first, other.name_first)
        General.pick_match_not_empty(self.name_last, other.name_last)
        General.pick_match_not_empty(self.election_code, other.election_code)
        General.pick_match_not_empty(self.assembly_code, other.assembly_code)
        General.pick_match_not_empty(self.electorate_code, other.electorate_code)
        General.pick_match_not_empty(self.ballot_code, other.ballot_code)

        self_party_code = self.party_code.replace(self.election_code, "")
        other_party_code = other.party_code.replace(other.election_code, "")
        indep = "-independent"
        if self_party_code.startswith(indep) and other_party_code.startswith(indep):
            self.party_code = General.pick_longest_str(
                self.party_code, other.party_code
            )
        else:
            General.pick_match_not_empty(self.party_code, other.party_code)

        title = General.pick_longest_str(self.title, other.title)
        result_codes = self.result_codes + other.result_codes
        notes = self.notes + other.notes

        self.title = title
        self.result_codes = General.merge_list_str(result_codes)
        self.notes = Note.normalise(notes)

    def add_to(self, collection: list["Candidate"]) -> None:
        existing = self.find_in(collection, self)
        if existing:
            existing.merge_in(self)
        else:
            collection.append(self)

    @classmethod
    def normalise(cls, collection: list["Candidate"]) -> list["Candidate"]:
        result = []
        for item in sorted(collection, key=lambda x: x.code):
            item.add_to(result)
        return result

    @classmethod
    def find_in(
        cls, collection: Collection["Candidate"], item: "Candidate"
    ) -> "Candidate":
        result = next((i for i in collection if i.code == item.code), None)
        return result
