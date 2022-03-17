from src.model.combination import Combination
from src.model.election import Election
from src.model.note import Note


class AEC:

    _input_aec_id_key = "AEC Election ID"
    _assembly_senate_code = "senate"
    _assembly_reps_code = "house-of-reps"

    def election_code(self, election: Election):
        election_code = next(
            (
                i.content
                for i in election.notes
                if i.category == Note.get_category_raw_info()
                and i.display == self._input_aec_id_key
            ),
            None,
        )

        if not election_code:
            raise ValueError("No AEC ID found.")
        return election_code

    def get_assembly_senate(self, combination: Combination):
        assemblies = combination.assemblies
        senate_code = self._assembly_senate_code
        senate = next((i for i in assemblies if senate_code in i.code), None)
        if not senate:
            raise ValueError(f"Must have an assembly with '{senate_code}' in the code.")
        return senate

    def get_assembly_house_reps(self, combination: Combination):
        assemblies = combination.assemblies
        reps_code = self._assembly_reps_code
        house_reps = next((i for i in assemblies if reps_code in i.code), None)
        if not house_reps:
            raise ValueError(f"Must have an assembly with '{reps_code}' in the code.")
        return house_reps

    def get_party_independent(self):
        return "independent"

    def get_party_independent_title(self):
        return "Independent"

    def get_party_independent_short(self):
        return "IND"
