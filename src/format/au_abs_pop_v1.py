from time import strptime
from typing import Optional

from src.helper.aec import AEC
from src.helper.general import General
from src.model.assembly import Assembly
from src.model.combination import Combination
from src.model.election import Election
from src.model.electorate import Electorate
from src.model.note import Note
from src.model.result import Result


class AuAbsPopV1:
    """Australia Electoral Commission candidates list (v1)."""

    excel_name = "32180DS0003_2010-20.xls"
    fed_electorates_2018_name = "abs-est-pop-fed-electorates-asgs-2018.tsv"
    fed_electorates_2021_name = "abs-est-pop-fed-electorates-asgs-2021.tsv"
    fed_electorates_name = "federal-electorates-pop"

    state_electorates_name = "state-electorates-pop"
    state_electorates_2020_name = "abs-est-pop-state-electorates-asgs-2020.tsv"

    def __init__(self, general: General, aec: AEC):
        self._general = general
        self._aec = aec
        self._cat_info = Note.get_category_raw_info()
        self._pop_code, self._pop_title = Result.population_code_title()
        self._enrol_code, _ = Result.enrolment_code_title()
        self._not_enrol_code, _ = Result.not_enrolled_code_title()
        self._cat_people = Result.category_people_count()

    def populate(
        self, original_data: dict, combination: Combination, election: Election
    ) -> None:
        """Populate the Combination with result data."""

        # TODO: election notes should specify which data source to use
        #       because the electorates can change, the data sources may have different electorates

        year = str(strptime(election.date, "%Y-%m-%d").tm_year)
        electorates = combination.electorates

        senate = self._aec.get_assembly_senate(combination)
        house_reps = self._aec.get_assembly_house_reps(combination)

        # federal pop
        for item in original_data.get(self.fed_electorates_name, []):
            div_id = item.get("CED code")
            name = item.get("CED name")
            raw = {"div_id": div_id, "name": name, "pop": int(item.get(year))}
            self._create_electorate(raw, house_reps, combination, None)

            if not div_id and name != "TOTAL AUSTRALIA":
                raise

        # state pop
        current = []
        for item in original_data.get(self.state_electorates_name, []):
            div_id = item.get("SED code")
            name = item.get("SED name")
            raw = {"div_id": div_id, "name": name, "pop": int(item.get(year))}
            current.append(raw)

            if not div_id:
                state_full_name = name.title().replace("Total", "").strip()
                state = next(
                    (
                        i
                        for i in electorates
                        if i.title == state_full_name
                        or any((n.content == state_full_name for n in i.notes))
                    ),
                    None,
                )
                self._create_electorates(current, senate, combination, state)
                current = []

    def _create_electorates(
        self,
        raw: list[dict],
        assembly: Assembly,
        combination: Combination,
        state: Electorate,
    ):
        for i in raw:
            self._create_electorate(i, assembly, combination, state)

    def _create_electorate(
        self,
        raw: dict,
        assembly: Assembly,
        combination: Combination,
        state: Optional[Electorate],
    ):
        div_id = raw.get("div_id")
        name = raw.get("name")
        pop = raw.get("pop")

        notes = [Note(display="division id", content=div_id, category=self._cat_info)]

        if state:
            notes.extend([n.copy() for n in state.notes])
            short = state.title
            name = f"{short} {name}"

        asb_code = assembly.code
        code = self._general.result_electorate_code(asb_code, name, self._pop_code)
        electorate_code = self._general.electorate_code(asb_code, name)
        ballot_code = self._general.ballot_code(asb_code, name)
        combination.add(
            Result(
                code=code,
                title=f"{name} {self._pop_title}".strip(),
                value=pop,
                category=self._cat_people,
                ancestor_codes=[],
                child_codes=[
                    self._general.result_electorate_code(
                        asb_code, name, self._enrol_code
                    ),
                    self._general.result_electorate_code(
                        asb_code, name, self._not_enrol_code
                    ),
                ],
                notes=notes,
                election_code=assembly.election_code,
                assembly_code=assembly.code,
                electorate_code=electorate_code,
                ballot_code=ballot_code,
            )
        )


# 'federal-electorates-pop' = {list: 152} [{'CED code': '101', 'CED name': 'Banks', '2010': '149465', '2011': '151226', '2012': '153241', '2013': '155532', '2014': '157800', '2015': '159798', '2016': '161694', '2017': '164539', '2018': '166548', '2019': '167990', '2020': '168731', 'blank': '', 'change amount 2019-2020': '741', 'change percent 2019-2020': '0.4'}, {'CED code': '102', 'CED name': 'Barton', '2010': '160845', '2011': '161929', '2012': '165788', '2013': '169718', '2014': '173645', '2015': '177782', '2016': '182374', '2017': '188059', '2018': '191292', '2019': '194496', '2020': '196485', 'blank': '', 'change amount 2019-2020': '1989', 'change percent 2019-2020': '1.0'}, {'CED code': '103', 'CED name': 'Bennelong', '2010': '154257', '2011': '156446', '2012': '160003', '2013': '163642', '2014': '167233', '2015': '171415', '2016': '175850', '2017': '181258', '2018': '186215', '2019': '191618', '2020': '194594', 'blank': '', 'change amount 2019-2020': '2976', 'change percent 2019-2020': '1.6'}, {'CED code': '104', 'CED n...
# 'state-electorates-pop' = {list: 442} [{'SED code': '10001', 'SED name': 'Albury', '2010': '76871', '2011': '77085', '2012': '77468', '2013': '78063', '2014': '78816', '2015': '79406', '2016': '80141', '2017': '81017', '2018': '81812', '2019': '82506', '2020': '83431', 'blank': '', 'change amount 2019-2020': '925', 'change percent 2019-2020': '1.1'}, {'SED code': '10002', 'SED name': 'Auburn', '2010': '90312', '2011': '91663', '2012': '94530', '2013': '98050', '2014': '101145', '2015': '104576', '2016': '108705', '2017': '113129', '2018': '117018', '2019': '120692', '2020': '122168', 'blank': '', 'change amount 2019-2020': '1476', 'change percent 2019-2020': '1.2'}, {'SED code': '10003', 'SED name': 'Ballina', '2010': '71213', '2011': '71415', '2012': '72265', '2013': '73196', '2014': '74073', '2015': '75068', '2016': '76324', '2017': '77344', '2018': '78510', '2019': '79485', '2020': '80791', 'blank': '', 'change amount 2019-2020': '1306', 'change percent 2019-2020': '1.6'}, {'SED code': '10004', 'SED name': 'Balmain', '2...
