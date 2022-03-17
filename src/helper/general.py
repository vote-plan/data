import logging
import re
from functools import reduce

from boltons.strutils import slugify


class General:
    def __init__(self):
        msg_fmt = "%(asctime)s [%(levelname)8s] %(message)s"
        date_fmt = "%Y-%m-%dT%H:%M:%S"
        logging.basicConfig(level=logging.INFO, format=msg_fmt, datefmt=date_fmt)
        self._logger = logging.getLogger("data")

    @property
    def log(self):
        """Get the logger."""
        return self._logger

    @property
    def _delim(self):
        return "-"

    @classmethod
    def pick_match_not_empty(cls, *args):
        seen = set()
        for i in args:
            if i is None or str(i).strip() == "":
                raise ValueError("Must not be empty.")
            seen.add(i)
        if len(seen) == 1:
            return list(seen)[0]
        else:
            raise ValueError(f"Must be the same value '{', '.join(sorted(seen))}'.")

    @classmethod
    def pick_match_allow_empty(cls, *args):
        seen = set()
        for i in args:
            if not i:
                continue
            seen.add(i)
        if not seen or len(seen) < 1:
            return ""
        elif len(seen) == 1:
            return list(seen)[0]
        else:
            raise ValueError(f"Must be the same value '{', '.join(sorted(seen))}'.")

    @classmethod
    def pick_longest_str(cls, *args: str):
        def longest(a, b):
            a = str(a) if a else ""
            b = str(b) if b else ""
            return a if len(a) >= len(b) else b

        result = reduce(longest, args)
        return result

    @classmethod
    def merge_list_str(cls, *args: list[str]):
        result = sorted(set(*args))
        return result

    def collapse_spaces(self, value: str):
        result = re.sub(r"\s+", " ", value or "")
        return result

    def get_bool(self, value: str):
        return value.strip().upper() == "Y"

    def party_code(self, election_code: str, party_title: str):
        if not party_title or not party_title.strip():
            raise ValueError()
        result = slugify(party_title.strip(), delim=self._delim)
        return self._delim.join([election_code, result])

    def electorate_code(self, assembly_code: str, electorate_title: str):
        if not electorate_title or not electorate_title.strip():
            return assembly_code

        result = slugify(electorate_title.strip(), delim=self._delim)
        return self._delim.join([assembly_code, result])

    def candidate_code(
        self, assembly_code: str, electorate_title: str, name_first: str, name_last: str
    ):
        if not name_first or not name_first.strip():
            raise ValueError()
        if not name_last or not name_last.strip():
            raise ValueError()
        name = f"{name_last.strip()} {name_first.strip()}".strip()
        result = slugify(name, delim=self._delim)
        electorate_code = self.electorate_code(assembly_code, electorate_title)
        return self._delim.join([electorate_code, result])

    def result_electorate_code(self, assembly_code: str, name: str, suffix: str):
        electorate_code = self.electorate_code(assembly_code, name)
        suffix = slugify(suffix, delim=self._delim)
        result = self._delim.join([electorate_code, suffix])
        return result

    def candidate_title(self, name_first: str, name_last: str):
        name_first = name_first.strip() if name_first else ""
        name_last = name_last.strip() if name_last else ""
        name = f"{name_first} {name_last}".strip()
        result = self.collapse_spaces(name if name else "")
        return result

    def electorate_title(self, value: str):
        result = self.collapse_spaces(value.strip() if value else "")
        return result

    def party_title(self, value: str):
        result = self.collapse_spaces(value.strip() if value else "")
        return result

    def ballot_code(self, assembly_code: str, electorate_title: str):
        electorate_code = self.electorate_code(assembly_code, electorate_title)
        return self._delim.join([electorate_code, "ballot"])

    def collect_unique(self, collect: dict, item: dict):
        for k, v in item.items():
            if k not in collect:
                collect[k] = set()
            collect[k].add(v)
