from dataclasses import dataclass
from typing import Collection

from dataclasses_json import dataclass_json, LetterCase

from src.helper.general import General
from src.model.note import Note


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Assembly:
    code: str
    title: str
    election_code: str
    electorate_codes: list[str]
    ballot_codes: list[str]
    notes: list[Note]

    @classmethod
    def get_code_senate(cls):
        return "senate"

    @classmethod
    def get_code_representatives(cls):
        return "representatives"

    def merge_in(self, other: "Assembly") -> None:
        General.pick_match_not_empty(self.code, other.code)
        General.pick_match_not_empty(self.election_code, other.election_code)

        title = General.pick_longest_str(self.title, other.title)
        ballot_codes = self.ballot_codes + other.ballot_codes
        electorate_codes = self.electorate_codes + other.electorate_codes
        notes = self.notes + other.notes

        self.title = title
        self.electorate_codes = General.merge_list_str(electorate_codes)
        self.ballot_codes = General.merge_list_str(ballot_codes)
        self.notes = Note.normalise(notes)

    def add_to(self, collection: list["Assembly"]) -> None:
        existing = self.find_in(collection, self)
        if existing:
            existing.merge_in(self)
        else:
            collection.append(self)

    @classmethod
    def normalise(cls, collection: list["Assembly"]) -> list["Assembly"]:
        result = []
        for item in sorted(collection, key=lambda x: x.code):
            item.add_to(result)
        return result

    @classmethod
    def find_in(
        cls, collection: Collection["Assembly"], item: "Assembly"
    ) -> "Assembly":
        result = next((i for i in collection if i.code == item.code), None)
        return result
