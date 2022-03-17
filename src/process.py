import importlib.resources
from pathlib import Path

from src.format.au_abs_pop_v1 import AuAbsPopV1
from src.helper.general import General
from src.model.combination import Combination
from src.model.election import Election
from src.model.note import Note
from src.store import Store


class Process:
    def __init__(self):
        self._general = General()
        self._general.log.info("Starting data init.")

        self.store = Store(self._general)

        with importlib.resources.files("raw") as p:
            self.raw_path = Path(p)
        with importlib.resources.files("ready") as p:
            self.ready_path = Path(p)
        with importlib.resources.files("src") as p:
            self.src_path = Path(p)

    def run(self) -> None:
        self._general.log.info("Starting data processing.")

        shared_path = self.raw_path / "shared" / "original.zip"
        shared_data = self.store.read_zip_file_list(shared_path)

        del shared_data[AuAbsPopV1.excel_name]
        del shared_data[AuAbsPopV1.fed_electorates_2018_name]
        shared_data[AuAbsPopV1.fed_electorates_name] = shared_data.pop(
            AuAbsPopV1.fed_electorates_2021_name
        )
        shared_data[AuAbsPopV1.state_electorates_name] = shared_data.pop(
            AuAbsPopV1.state_electorates_2020_name
        )

        c = Combination.build_empty()

        for current_dir in self.raw_path.iterdir():
            if not current_dir.is_dir() or current_dir.name == "shared":
                continue

            input_path = current_dir / "input.json"

            if input_path.exists():
                self._general.log.debug(f"Read input: {input_path}")
                input_data = self.store.read_json_file(input_path)
            else:
                input_data = {}

            original_path = current_dir / "original.zip"
            if original_path.exists():
                self._general.log.debug(f"Read original: {original_path}")
                original_data = self.store.read_zip_file_list(original_path)
            else:
                original_data = {}

            another = self.build({**shared_data, **original_data}, input_data)
            if another:
                c.merge_in(another)

        self._general.log.info(f"Writing ready files.")

        # write everything to a json file
        all_file = self.ready_path / "all.json"
        self._write_combination_json(all_file, c)

        # test reading
        self._read_combination_json(all_file)

        # write each election to separate json files
        for election in c.elections:
            ec = election.code
            election_file = self.ready_path / election.code
            election_file = election_file.with_suffix(".json")
            obj = Combination(
                assemblies=[i for i in c.assemblies if i.election_code == ec],
                ballots=[i for i in c.ballots if i.election_code == ec],
                candidates=[i for i in c.candidates if i.election_code == ec],
                elections=[election],
                electorates=[i for i in c.electorates if i.election_code == ec],
                parties=[i for i in c.parties if i.election_code == ec],
                results=[i for i in c.results if i.election_code == ec],
            )
            if obj.any():
                self._write_combination_json(election_file, obj)

        # write each combination property to separate file
        sep_files = {
            "assemblies": c.assemblies,
            "ballots": c.ballots,
            "candidates": c.candidates,
            "elections": c.elections,
            "electorates": c.electorates,
            "parties": c.parties,
            "results": c.results,
        }
        for k, v in sep_files.items():
            file = self.ready_path / f"{k}.json"
            obj = Combination(
                assemblies=v if k == "assemblies" else [],
                ballots=v if k == "ballots" else [],
                candidates=v if k == "candidates" else [],
                elections=v if k == "elections" else [],
                electorates=v if k == "electorates" else [],
                parties=v if k == "parties" else [],
                results=v if k == "results" else [],
            )
            self._write_combination_json(file, obj)

        self._general.log.info("Finished data processing.")

    def build(self, original_data: dict, input_data: dict) -> Combination:
        result: Combination = None

        # must have both data sources
        if not input_data:
            return result

        combination: Combination = Combination.from_dict(input_data)
        for election in combination.elections:
            self.election(original_data, combination, election)

        return combination

    def election(
        self, original_data: dict, combination: Combination, election: Election
    ) -> None:
        """Populate the Combination with election data."""

        # load the parser class
        parser_info = next(
            (
                note
                for note in (election.notes or [])
                if note.category == Note.get_category_raw_parser()
            ),
            None,
        )
        if not parser_info:
            return

        parser_name = parser_info.content
        if parser_name:
            parser_class = self.store.get_parser(self.src_path / "parser", parser_name)
        else:
            parser_class = None

        if parser_class is None:
            return

        # run the parser
        self._general.log.info(f"Parsing {election.code} using {parser_name}.")
        parser = parser_class(self._general)
        parser.populate(original_data, combination, election)

    def _write_combination_json(self, path: Path, obj: Combination):
        with open(path, "wt") as f:
            f.write(Combination.schema().dumps(obj, sort_keys=True))

    def _read_combination_json(self, path: Path):
        with open(path, "rt") as f:
            Combination.schema().loads(f.read())


if __name__ == "__main__":

    def main():
        Process().run()
