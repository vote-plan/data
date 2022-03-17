from src.helper.aec import AEC
from src.helper.general import General
from src.model.assembly import Assembly
from src.model.ballot import Ballot
from src.model.candidate import Candidate
from src.model.combination import Combination
from src.model.election import Election
from src.model.electorate import Electorate
from src.model.party import Party
from src.model.result import Result


class AuAecMediaFeedStandardVerboseV1:
    """Australia Electoral Commission media feed standard verbose (v1)."""

    _ns_si = "{http://www.w3.org/2001/XMLSchema-instance}"
    _ns_mf = "{http://www.aec.gov.au/xml/schema/mediafeed}"
    _ns_eml = "{urn:oasis:names:tc:evs:schema:eml}"

    _input_aec_id_key = "AEC Election ID"

    def __init__(self, general: General, aec: AEC):
        self._general = general
        self._aec = aec

    def populate(
        self, original_data: dict, combination: Combination, election: Election
    ) -> None:
        """Populate the Combination with election data."""

        assemblies: list[Assembly] = []
        ballots: list[Ballot] = []
        candidates: list[Candidate] = []
        elections: list[Election] = []
        electorates: list[Electorate] = []
        parties: list[Party] = []
        results: list[Result] = []

        aec_code = self._aec.election_code(election)
        filename = f"aec-mediafeed-results-standard-verbose-{aec_code}.xml"
        original = original_data.get(filename)
        if original:
            self._media_feed(combination, original)

    def get_assemblies(self):
        pass

    def get_parties(self):
        pass

    def get_notes(self):
        pass

    def _media_feed(self, combination: Combination, d: dict):
        t = d["tag"]
        assert t == f"{self._ns_mf}MediaFeed"

        a = d["attributes"]
        c = d["children"]
        result = {
            "id": a.get("Id"),
            "created": a.get("Created"),
            "schema_version": a.get("SchemaVersion"),
            "eml_version": a.get("EmlVersion"),
            "schema_location": a.get(f"{self._ns_si}schemaLocation"),
            "managing_auth": self._get_managing_auth(
                next(
                    (i for i in c if i["tag"] == f"{self._ns_mf}ManagingAuthority"), {}
                )
            ),
            "language": next(
                (i["text"] for i in c if i["tag"] == f"{self._ns_mf}MessageLanguage"),
                None,
            ),
            "generator": self._get_msg_generator(
                next((i for i in c if i["tag"] == f"{self._ns_mf}MessageGenerator"), {})
            ),
            "cycle": next(
                (
                    {"id": i["text"], "created": i["attributes"].get("Created")}
                    for i in c
                    if i["tag"] == f"{self._ns_mf}Cycle"
                ),
                {},
            ),
            "results": self._get_results(
                next((i for i in c if i["tag"] == f"{self._ns_mf}Results"), {})
            ),
        }
        return result

    def _get_managing_auth(self, d: dict):
        t = d["tag"]
        assert t == f"{self._ns_mf}ManagingAuthority"

        c = d["children"]
        return [self._get_auth_id(i) for i in c]

    def _get_auth_id(self, d: dict):
        t = d["tag"]
        assert t == f"{self._ns_eml}AuthorityIdentifier"

        a = d["attributes"]
        return {"id": a.get("Id"), "text": d.get("text")}

    def _get_msg_generator(self, d: dict):
        t = d["tag"]
        assert t == f"{self._ns_mf}MessageGenerator"

        c = d["children"]
        return dict([(i["tag"].replace(self._ns_mf, "").lower(), i["text"]) for i in c])

    def _get_results(self, d: dict):
        t = d["tag"]
        assert t == f"{self._ns_mf}Results"

        a = d["attributes"]
        c = d["children"]

        event = next((i for i in c if i["tag"] == f"{self._ns_eml}EventIdentifier"), {})

        e = f"{self._ns_mf}Election"

        result = {
            "updated": a.get("Updated"),
            "phase": a.get("Phase"),
            "verbosity": a.get("Verbosity"),
            "granularity": a.get("Granularity"),
            "id": event["attributes"].get("Id"),
            "title": next(
                (
                    i["text"]
                    for i in event["children"]
                    if i["tag"] == f"{self._ns_eml}EventName"
                ),
                None,
            ),
            "representatives": self._get_representatives(
                next(
                    (
                        i
                        for i in c
                        if i["tag"] == e and i["children"][0]["attributes"]["Id"] == "H"
                    )
                )
            ),
            "senate": self._get_senate(
                next(
                    (
                        i
                        for i in c
                        if i["tag"] == e and i["children"][0]["attributes"]["Id"] == "S"
                    )
                )
            ),
        }
        return result

    def _get_representatives(self, d: dict):
        #         'tag' = {str} '{http://www.aec.gov.au/xml/schema/mediafeed}Election'
        # 'attributes' = {dict: 1} {'Updated': '2019-07-11T13:58:18'}
        pass

    def _get_senate(self, d: dict):
        pass
