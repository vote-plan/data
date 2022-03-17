from dataclasses import dataclass
from typing import Type, Union

from dataclasses_json import dataclass_json, LetterCase

from src.model.assembly import Assembly
from src.model.ballot import Ballot
from src.model.candidate import Candidate
from src.model.election import Election
from src.model.electorate import Electorate
from src.model.party import Party
from src.model.result import Result


CombinationTypes = Type[
    Union[Assembly, Ballot, Candidate, Election, Electorate, Party, Result]
]
CombinationInstances = Union[
    Assembly, Ballot, Candidate, Election, Electorate, Party, Result
]


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Combination:
    assemblies: list[Assembly]
    ballots: list[Ballot]
    candidates: list[Candidate]
    elections: list[Election]
    electorates: list[Electorate]
    parties: list[Party]
    results: list[Result]

    @classmethod
    def build_empty(cls):
        return Combination(
            assemblies=[],
            ballots=[],
            candidates=[],
            elections=[],
            electorates=[],
            parties=[],
            results=[],
        )

    def merge_in(self, other: "Combination") -> None:
        self.assemblies = Assembly.normalise(self.assemblies + other.assemblies)
        self.ballots = Ballot.normalise(self.ballots + other.ballots)
        self.candidates = Candidate.normalise(self.candidates + other.candidates)
        self.elections = Election.normalise(self.elections + other.elections)
        self.electorates = Electorate.normalise(self.electorates + other.electorates)
        self.parties = Party.normalise(self.parties + other.parties)
        self.results = Result.normalise(self.results + other.results)

    def any(self):
        lists = [
            self.assemblies,
            self.ballots,
            self.candidates,
            self.elections,
            self.electorates,
            self.parties,
            self.results,
        ]
        return any(lists)

    def find(self, item_type: CombinationTypes, *args, **kwargs):
        """Find an item of the given type matching the given filters."""
        if item_type not in CombinationTypes:
            raise
        return item_type.find(*args, **kwargs)

    def add(self, item: CombinationInstances) -> None:
        """Add the item."""
        if not item:
            raise ValueError("Must pass an item.")
        if not item.code:
            raise ValueError("Must set code.")

        if isinstance(item, Assembly):
            collection = self.assemblies
        elif isinstance(item, Ballot):
            collection = self.ballots
        elif isinstance(item, Candidate):
            collection = self.candidates
        elif isinstance(item, Election):
            collection = self.elections
        elif isinstance(item, Electorate):
            collection = self.electorates
        elif isinstance(item, Party):
            collection = self.parties
        elif isinstance(item, Result):
            collection = self.results
        else:
            raise

        item.add_to(collection)
