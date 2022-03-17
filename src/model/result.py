from dataclasses import dataclass
from typing import Collection

from dataclasses_json import dataclass_json, LetterCase

from src.helper.general import General
from src.model.note import Note


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Result:
    """An individual result in an election."""

    code: str
    title: str

    value: int
    """The number of votes or number of voters."""

    category: str
    """The category of this result: 'candidate_elected', 'candidate_excluded', 'people_count'."""

    ancestor_codes: list[str]
    child_codes: list[str]

    notes: list[Note]

    election_code: str
    assembly_code: str
    electorate_code: str
    ballot_code: str

    @classmethod
    def category_candidate_elected(cls):
        return "candidate_elected"

    @classmethod
    def category_candidate_excluded(cls):
        return "candidate_excluded"

    @classmethod
    def category_people_count(cls):
        return "people_count"

    @classmethod
    def population_code_title(cls):
        return "population", "Population"

    @classmethod
    def enrolment_code_title(cls):
        return "enrolment", "Enrolment"

    @classmethod
    def not_enrolled_code_title(cls):
        return "not-enrolled", "Not Enrolled"

    @classmethod
    def participated_code_title(cls):
        # 'turnout'
        return "participated", "Participated"

    @classmethod
    def not_participated_code_title(cls):
        return "not-participated", "Did not participate"

    @classmethod
    def voted_code_title(cls):
        return "voted", "Voted"

    @classmethod
    def not_voted_code_title(cls):
        return "not-voted", "Did not vote"

    @classmethod
    def formal_code_title(cls):
        return "formal", "Formal votes"

    @classmethod
    def not_formal_code_title(cls):
        return "not-formal", "Informal votes"

    def merge_in(self, other: "Result") -> None:
        General.pick_match_not_empty(self.code, other.code)
        General.pick_match_not_empty(self.category, other.category)
        General.pick_match_not_empty(self.value, other.value)

        ancestor_codes = self.ancestor_codes + other.ancestor_codes
        child_codes = self.child_codes + other.child_codes
        notes = self.notes + other.notes

        self.title = General.pick_longest_str(self.title, other.title)
        self.ancestor_codes = General.merge_list_str(ancestor_codes)
        self.child_codes = General.merge_list_str(child_codes)
        self.notes = Note.normalise(notes)

    def add_to(self, collection: list["Result"]) -> None:
        existing = self.find_in(collection, self)
        if existing:
            existing.merge_in(self)
        else:
            collection.append(self)

    @classmethod
    def normalise(cls, collection: list["Result"]) -> list["Result"]:
        result = []
        for item in sorted(collection, key=lambda x: x.code):
            item.add_to(result)
        return result

    @classmethod
    def find_in(cls, collection: Collection["Result"], item: "Result") -> "Result":
        result = next((i for i in collection if i.code == item.code), None)
        return result
