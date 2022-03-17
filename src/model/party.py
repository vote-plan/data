from dataclasses import dataclass
from typing import Collection

from dataclasses_json import dataclass_json, LetterCase

from src.helper.general import General
from src.model.note import Note


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Party:
    code: str
    short_name: str
    title: str
    alt_titles: list[str]
    category: str
    notes: list[Note]

    election_code: str
    candidate_codes: list[str]

    @classmethod
    def get_category_named(cls):
        return "named"

    @classmethod
    def get_category_not_named(cls):
        return "not-named"

    @classmethod
    def get_category_not_grouped(cls):
        return "not-grouped"

    def merge_in(self, other: "Party") -> None:
        General.pick_match_not_empty(self.code, other.code)
        General.pick_match_not_empty(self.election_code, other.election_code)
        General.pick_match_allow_empty(self.category, other.category)

        self.title = General.pick_longest_str(self.title, other.title)
        self.notes = Note.normalise(self.notes + other.notes)
        self.candidate_codes = General.merge_list_str(
            self.candidate_codes + other.candidate_codes
        )

    def add_to(self, collection: list["Party"]) -> None:
        existing = self.find_in(collection, self)
        if existing:
            existing.merge_in(self)
        else:
            collection.append(self)

    @classmethod
    def normalise(cls, collection: list["Party"]) -> list["Party"]:
        result = []
        for item in sorted(collection, key=lambda x: x.code):
            item.add_to(result)
        return result

    @classmethod
    def find_in(cls, collection: Collection["Party"], item: "Party") -> "Party":
        result = next((i for i in collection if i.code == item.code), None)
        return result
