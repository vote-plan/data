from dataclasses import dataclass
from typing import Collection

from boltons.strutils import slugify
from dataclasses_json import dataclass_json, LetterCase

from src.helper.general import General


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Note:
    """A custom note that provides a tuple of text information."""

    display: str
    """The displayed text."""

    content: str
    """The content or internal text."""

    category: str
    """The category helps determine what can be done with this note."""

    @classmethod
    def get_category_raw_info(cls):
        return "raw-info"

    @classmethod
    def get_category_raw_url(cls):
        return "raw-url"

    @classmethod
    def get_category_raw_parser(cls):
        return "raw-parser"

    @classmethod
    def get_category_info_url(cls):
        return "raw-url"

    @property
    def order_id(self):
        d = "-"
        return d.join(
            [
                slugify(self.category, delim=d),
                slugify(self.display, delim=d),
                slugify(self.content, delim=d),
            ]
        )

    def copy(self):
        return Note(display=self.display, content=self.content, category=self.category)

    def merge_in(self, other: "Note") -> None:
        General.pick_match_not_empty(self.display, other.display)
        General.pick_match_not_empty(self.content, other.content)
        General.pick_match_not_empty(self.category, other.category)

    def add_to(self, collection: list["Note"]) -> None:
        existing = self.find_in(collection, self)
        if existing:
            existing.merge_in(self)
        else:
            collection.append(self)

    @classmethod
    def normalise(cls, collection: list["Note"]) -> list["Note"]:
        result = []
        for item in sorted(collection, key=lambda x: x.order_id):
            item.add_to(result)
        return result

    @classmethod
    def find_in(cls, collection: Collection["Note"], item: "Note") -> "Note":
        result = next(
            (
                i
                for i in collection
                if i.display == item.display
                and i.content == item.content
                and i.category == item.category
            ),
            None,
        )
        return result
