import typing
from dataclasses import dataclass

from dataclasses_json import dataclass_json, LetterCase

from src.helper.general import General
from src.model.note import Note


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Electorate:
    code: str
    title: str
    ballot_codes: list[str]
    notes: list[Note]

    election_code: str
    assembly_code: str
    candidate_codes: list[str]

    def merge_in(self, other: "Electorate") -> None:
        General.pick_match_not_empty(self.code, other.code)
        General.pick_match_not_empty(self.election_code, other.election_code)

        ballot_codes = self.ballot_codes + other.ballot_codes
        assembly_codes = [self.assembly_code, other.assembly_code]
        candidate_codes = self.candidate_codes + other.candidate_codes
        notes = self.notes + other.notes

        self.title = General.pick_longest_str(self.title, other.title)
        self.ballot_codes = General.merge_list_str(ballot_codes)
        self.notes = Note.normalise(notes)
        self.assembly_code = General.pick_match_allow_empty(*assembly_codes)
        self.candidate_codes = General.merge_list_str(candidate_codes)

    def add_to(self, collection: list["Electorate"]) -> None:
        existing = self.find_in(collection, self)
        if existing:
            existing.merge_in(self)
        else:
            collection.append(self)

    @classmethod
    def normalise(cls, collection: list["Electorate"]) -> list["Electorate"]:
        result = []
        for item in sorted(collection, key=lambda x: x.code):
            item.add_to(result)
        return result

    @classmethod
    def find_in(
        cls, collection: typing.Collection["Electorate"], item: "Electorate"
    ) -> "Electorate":
        result = next((i for i in collection if i.code == item.code), None)
        return result
