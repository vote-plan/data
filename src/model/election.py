from dataclasses import dataclass
from typing import Collection

from dataclasses_json import dataclass_json, LetterCase

from src.helper.general import General
from src.model.note import Note


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Election:
    code: str
    title: str

    location_country: str
    location_administrative_area_name: str
    location_locality_name: str
    location_description: str

    date: str
    date_time_zone: str

    assembly_codes: list[str]
    party_codes: list[str]
    notes: list[Note]

    @classmethod
    def get_input_data_key(cls):
        return "input"

    def merge_in(self, other: "Election") -> None:
        General.pick_match_not_empty(self.code, other.code)
        General.pick_match_not_empty(self.location_country, other.location_country)
        General.pick_match_not_empty(
            self.location_administrative_area_name,
            other.location_administrative_area_name,
        )
        General.pick_match_not_empty(
            self.location_locality_name, other.location_locality_name
        )
        General.pick_match_not_empty(
            self.location_description, other.location_description
        )
        General.pick_match_not_empty(self.date, other.date)
        General.pick_match_not_empty(self.date_time_zone, other.date_time_zone)

        title = General.pick_longest_str(self.title, other.title)
        assembly_codes = self.assembly_codes + other.assembly_codes
        party_codes = self.party_codes + other.party_codes
        notes = self.notes + other.notes

        self.title = title
        self.assembly_codes = assembly_codes
        self.party_codes = party_codes
        self.notes = Note.normalise(notes)

    def add_to(self, collection: list["Election"]) -> None:
        existing = self.find_in(collection, self)
        if existing:
            existing.merge_in(self)
        else:
            collection.append(self)

    @classmethod
    def normalise(cls, collection: list["Election"]) -> list["Election"]:
        result = []
        for item in sorted(collection, key=lambda x: x.code):
            item.add_to(result)
        return result

    @classmethod
    def find_in(
        cls, collection: Collection["Election"], item: "Election"
    ) -> "Election":
        result = next((i for i in collection if i.code == item.code), None)
        return result
