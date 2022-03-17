import requests_cache
from parsel import Selector

from src.helper.general import General
from src.model.assembly import Assembly
from src.model.ballot import Ballot
from src.model.candidate import Candidate
from src.model.combination import Combination
from src.model.election import Election
from src.model.electorate import Electorate
from src.model.note import Note
from src.model.party import Party


class AuEcsaV1:

    _assembly_lc = "legislative-council"
    _assembly_ha = "house-of-assembly"

    def __init__(self, general: General):
        self._general = general
        self._rs = requests_cache.CachedSession("au-ecsa-v1-cache", backend="sqlite")
        self._rs_headers = {
            "user-agent": "vote-plan-data (+https://github.com/vote-plan)"
        }

        # used xpdf\bin64\pdftotext.exe -table -enc "UTF-8" "HA candidate contacts.pdf" "candidates-ha-pdf.txt"
        # used xpdf\bin64\pdftotext.exe -table -enc "UTF-8" "LC candidate contacts.pdf" "candidates-lc-pdf.txt"

    def populate(
        self, original_data: dict, combination: Combination, election: Election
    ) -> None:
        """Populate the Combination with election data."""

        party_map = dict(
            [(p["long"], p["short"]) for p in original_data.get("parties.csv", {})]
        )
        a = combination.assemblies
        e = election.code
        lc = next((i for i in a if self._assembly_lc in i.code and e in i.code), None)
        ha = next((i for i in a if self._assembly_ha in i.code and e in i.code), None)

        ha_pdf = self._get_ha_pdf(original_data, ha)
        ha_web = self._get_ha_web(original_data, ha)
        lc_pdf = self._get_lc_pdf(original_data, lc)
        lc_web = self._get_lc_web(original_data, lc)

        self._create(ha_pdf + ha_web + lc_pdf + lc_web, party_map, combination)

    def _get_party_category(self, value: str):
        if value == "grouped":
            return Party.get_category_named()
        elif value == "grouped-ind":
            return Party.get_category_not_named()
        elif value == "ungrouped-ind":
            return Party.get_category_not_grouped()
        else:
            raise ValueError()

    def _get_sitting(self, value: str):
        value = (value or "").strip()
        if value == "*" or value == "#":
            return True
        else:
            return False

    def _notes(self, *arg: Note) -> list[Note]:
        return [n for n in arg if n.content]

    def _get_lc_pdf(self, original_data: dict, assembly: Assembly):
        data = []

        party_named = "groupedcandidates"
        party_not_named = "independentgrouped"
        party_not_grouped = "independentungrouped"

        headers = {
            "Group": None,
            "Full name": None,
            "Contact": None,
            "Affiliation": None,
            "member": None,
        }
        current_group = None
        for line in original_data.get("candidates-lc-pdf.txt", "").splitlines():
            if not line or not line.strip():
                continue

            line_s = line.strip().replace(" ", "").lower()
            if line_s.startswith("page") and "of" in line_s and line_s[-1].isnumeric():
                continue
            elif "denotesmember" in line_s or "stateelection" in line_s:
                continue
            elif "legislativecouncil" in line_s or "sitting" == line_s:
                continue
            elif line_s.startswith(party_named):
                current_group = Party.get_category_named()
                continue
            elif line_s.startswith(party_not_named):
                current_group = Party.get_category_not_named()
                continue
            elif line_s.startswith(party_not_grouped):
                current_group = Party.get_category_not_grouped()
                continue
            elif all(h in line for h in headers.keys()):
                for k, v in headers.items():
                    headers[k] = line.index(k)
            elif any(v is None for k, v in headers.items()):
                continue
            else:
                keys = sorted(headers.items(), key=lambda x: x[1])
                last_index = len(keys) - 1

                if not current_group:
                    raise ValueError()

                item = {"party_grouping": current_group, "assembly": assembly}
                for index, (header, offset) in enumerate(keys):
                    start_index = offset

                    if index != last_index:
                        stop_index = keys[index + 1][1]
                        text = line[start_index:stop_index].strip()
                    else:
                        text = line[start_index:].strip()

                    item[header] = text
                data.append(item)

        return data

    def _get_lc_web(self, original_data: dict, assembly: Assembly):
        data = []

        party_named = "groupedcandidates"
        party_not_named = "independentgrouped"
        party_not_grouped = "independentungrouped"

        url = original_data.get("candidates-lc-web.txt", "").strip()
        r = self._rs.get(url, headers=self._rs_headers)
        selector = Selector(text=r.text)

        h2s = selector.xpath("//h2")

        seen_titles = []
        for h2 in h2s:
            title = h2.xpath("text()").get().strip().replace(" ", "").lower()
            if title in seen_titles:
                continue
            seen_titles.append(title)

            if title.startswith(party_named):
                party_grouping = Party.get_category_named()
            elif title.startswith(party_not_named):
                party_grouping = Party.get_category_not_named()
            elif title.startswith(party_not_grouped):
                party_grouping = Party.get_category_not_grouped()
            else:
                raise ValueError()

            table = h2.xpath("following::table")[0]
            headers = table.xpath("thead//th/text()")
            rows = table.xpath("tbody/tr")
            for row in rows:
                items = row.xpath("td//text()")
                data_item = {"party_grouping": party_grouping, "assembly": assembly}
                for header, item in zip(headers, items):
                    data_item[header.get().strip()] = item.get().strip()
                data.append(data_item)

        return data

    def _get_ha_pdf(self, original_data: dict, assembly: Assembly):
        data = []
        headers: dict[str, int] = {
            "Full name": None,
            "Gender": None,
            "Contact number": None,
            "Affiliation": None,
        }
        current_electorate = None
        for line in original_data.get("candidates-ha-pdf.txt", "").splitlines():
            if not line or not line.strip():
                continue
            line_s = line.strip()
            if line_s.startswith("©") or line_s[-1].isnumeric() or line_s.endswith("#"):
                continue
            elif all(h in line for h in headers.keys()):
                for k, v in headers.items():
                    headers[k] = line.index(k)
            elif any(v is None for k, v in headers.items()):
                continue
            elif len(line) < max([v for k, v in headers.items()]):
                continue
            else:
                keys = sorted(headers.items(), key=lambda x: x[1])
                full_name = keys[0]
                keys.insert(0, ("Electorate", 0))
                keys.insert(1, ("Setting member", full_name[1] - 3))
                last_index = len(keys) - 1

                item = {"assembly": assembly}
                for index, (header, offset) in enumerate(keys):
                    start_index = offset

                    if index != last_index:
                        stop_index = keys[index + 1][1]
                        text = line[start_index:stop_index].strip()
                    else:
                        text = line[start_index:].strip()

                    if header == "Electorate" and text:
                        current_electorate = text
                    elif current_electorate and header == "Electorate" and not text:
                        text = current_electorate

                    item[header] = text
                data.append(item)

        return data

    def _get_ha_web(self, original_data: dict, assembly: Assembly):
        data = []
        for entry in original_data.get("candidates-ha-web.csv", []):
            url = entry["url"]
            electorate = entry["electorate"]
            r = self._rs.get(url, headers=self._rs_headers)
            selector = Selector(text=r.text)

            headers = selector.xpath("//table/thead//th/text()")
            rows = selector.xpath("//table/tbody/tr")
            for row in rows:
                items = row.xpath("td//text()")
                data_item = {"electorate": electorate, "assembly": assembly}
                for header, item in zip(headers, items):
                    data_item[header.get().strip()] = item.get().strip()
                data.append(data_item)
        return data

    def _create(self, rows: list[dict], parties: dict, combination: Combination):
        g = self._general
        cat = Note.get_category_raw_info()
        for row in rows:
            assembly: Assembly = row.get("assembly")
            position = row.get("Position", "").strip()
            party_grouping = row.get("party_grouping", "").strip()
            group = row.get("Group", "").strip()
            gender = self._gender(row.get("Gender", "").strip())
            contact = g.collapse_spaces(
                row.get("Contact number", "").strip() or row.get("Contact", "").strip()
            )

            name_last, name_first = row.get("Full name", ",").strip().split(",")
            name_first = row.get("Given name/s", "").strip() or name_first.strip()
            name_last = row.get("Surname", "").strip() or name_last.strip()

            electorate_title = (
                row.get("Electorate", "").strip() or row.get("electorate", "").strip()
            )
            electorate_title = g.collapse_spaces(electorate_title.title())

            sitting = (
                row.get("Setting member", "").strip()
                or row.get("Sitting member", "").strip()
                or row.get("member", "").strip()
            )
            sitting = "yes" if sitting else ""

            party_title = g.collapse_spaces(
                row.get("Affiliation", "").strip()
                or row.get("Affiliation or group", "").strip()
            )
            party_long, party_short = self._party_titles(parties, party_title)

            electorate_code = g.electorate_code(assembly.code, electorate_title)
            candidate_code = g.candidate_code(
                assembly.code, electorate_title, name_first, name_last
            )
            candidate_title = g.candidate_title(name_first, name_last)
            party_code = g.party_code(assembly.election_code, party_long)
            ballot_code = g.ballot_code(assembly.code, electorate_title)

            combination.add(
                Party(
                    code=party_code,
                    short_name=party_short,
                    title=party_long,
                    alt_titles=[],
                    category=party_grouping,
                    notes=[],
                    election_code=assembly.election_code,
                    candidate_codes=[candidate_code],
                )
            )
            combination.add(
                Candidate(
                    code=candidate_code,
                    title=candidate_title,
                    name_first=name_first,
                    name_last=name_last,
                    notes=self._notes(
                        Note(display="group", content=group, category=cat),
                        Note(display="position", content=position, category=cat),
                        Note(display="gender", content=gender, category=cat),
                        Note(display="contact", content=contact, category=cat),
                        Note(display="sitting", content=sitting, category=cat),
                        Note(display="party short", content=party_short, category=cat),
                        Note(display="party long", content=party_long, category=cat),
                    ),
                    election_code=assembly.election_code,
                    assembly_code=assembly.code,
                    electorate_code=electorate_code,
                    party_code=party_code,
                    ballot_code=ballot_code,
                    result_codes=[],
                )
            )
            combination.add(
                Electorate(
                    code=electorate_code,
                    title=electorate_title,
                    ballot_codes=[ballot_code],
                    notes=[],
                    election_code=assembly.election_code,
                    assembly_code=assembly.code,
                    candidate_codes=[candidate_code],
                )
            )
            combination.add(
                Ballot(
                    code=ballot_code,
                    category=Ballot.get_category_candidate(),
                    group_candidates_by_party=self._assembly_lc in assembly.code,
                    order_method=Ballot.get_order_fixed(),
                    notes=[],
                    election_code=assembly.election_code,
                    assembly_code=assembly.code,
                    electorate_code=electorate_code,
                    party_codes=[party_code],
                    candidate_codes=[candidate_code],
                    result_codes=[],
                )
            )

    def _party_titles(self, parties: dict, party_title: str):
        party_long = next((k for k, v in parties.items() if v == party_title), None)
        party_short = parties.get(party_title)
        if not party_long and not party_short:
            raise ValueError(f"Unknown party '{party_title}'.")
        elif party_long and party_short:
            raise ValueError(
                "Invalid party mapping for "
                f"'{party_long}', '{party_short}', '{party_title}'."
            )
        elif party_long and not party_short:
            party_short = party_title
        elif not party_long and party_short:
            party_long = party_title

        return party_long, party_short

    def _gender(self, value: str):
        value = (value or "").strip().lower()
        if not value:
            return ""
        elif value == "f":
            return "female"
        elif value == "m":
            return "male"
        else:
            raise ValueError()
