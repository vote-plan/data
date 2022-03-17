import csv
import json
import pkgutil
import zipfile
from importlib import import_module
from json import JSONDecodeError
from pathlib import Path
from typing import Union
from xml.etree import ElementTree
from xml.etree.ElementTree import Element

from src.helper.general import General


class Store:
    """Read data from various storage formats."""

    def __init__(self, general: General):
        self._general = general

    def read_xml_content(self, content: str) -> dict:
        """Read the xml into a tree structure."""
        root = ElementTree.fromstring(content)
        return self.read_xml_et(root)

    def read_xml_file(self, path: Path) -> dict:
        """Read a xml file."""
        tree = ElementTree.parse(path)
        root = tree.getroot()
        return self.read_xml_et(root)

    def read_xml_et(self, element: Element) -> dict:
        """convert a xml ElementTree into nested dicts."""
        return {
            "tag": element.tag,
            "attributes": element.attrib,
            "text": (element.text or "").strip(),
            "tail": (element.tail or "").strip(),
            "children": [self.read_xml_et(child) for child in element],
        }

    def read_json_content(self, content: str) -> Union[list, dict]:
        """Read the json."""
        # allow for empty content
        return json.loads(content) if content else {}

    def read_json_file(self, path: Path) -> Union[list, dict]:
        """Read the json file."""
        with open(path, "r") as f:
            try:
                return json.load(f)
            except JSONDecodeError as e:
                if str(e) == "Expecting value: line 1 column 1 (char 0)":
                    # allow for empty content
                    return {}
                else:
                    raise

    def read_csv_content(self, content: str) -> list[dict]:
        """Read the csv into rows."""
        lines = content.splitlines()
        lines = [line for line in lines if "," in line]
        return [i for i in csv.DictReader(lines, dialect="excel")]

    def read_csv_file(self, path: Path) -> list[dict]:
        """Read the csv file into rows."""
        content = self.read_text_file(path)
        return self.read_csv_content(content)

    def read_tsv_content(self, content: str) -> list[dict]:
        """Read the tsv into rows."""
        lines = content.splitlines()
        lines = [line for line in lines if "\t" in line]
        return [i for i in csv.DictReader(lines, dialect="excel-tab")]

    def read_tsv_file(self, path: Path) -> list[dict]:
        """Read the tsv file into rows."""
        content = self.read_text_file(path)
        return self.read_tsv_content(content)

    def read_text_file(self, path: Path) -> str:
        """Read the text file."""
        return self.try_read_text(path)

    def read_text_zip_file(self, path: Path, file: str) -> str:
        """Read a file in a zip file as text."""
        with zipfile.ZipFile(path, "r") as f:
            content_path = zipfile.Path(f) / file
            return self.try_read_text(content_path)

    def read_zip_file_list(self, path: Path) -> dict:
        """Read the files in a zip file."""
        result = {}
        filenames = self.get_zip_file_list(path)
        for filename in filenames:
            if filename.endswith(".csv"):
                original_file_content = self.read_text_zip_file(path, filename)
                result[filename] = self.read_csv_content(original_file_content)

            elif filename.endswith(".tsv"):
                original_file_content = self.read_text_zip_file(path, filename)
                result[filename] = self.read_tsv_content(original_file_content)

            elif filename.endswith(".xml"):
                original_file_content = self.read_text_zip_file(path, filename)
                result[filename] = self.read_xml_content(original_file_content)

            elif filename.endswith(".txt"):
                result[filename] = self.read_text_zip_file(path, filename)

            else:
                result[filename] = f"Unknown extension for file '{filename}'."
        return result

    def get_zip_file_list(self, path: Path) -> list[str]:
        """Get the filenames in a zip file."""
        with zipfile.ZipFile(path, "r") as f:
            return [i.name for i in zipfile.Path(f).iterdir() if i.is_file()]

    def get_parser(self, parser_dir: Path, find_name: str):
        results = pkgutil.iter_modules(path=[str(parser_dir)], prefix="")
        module_name, class_name = find_name.split(".")
        for finder, name, is_pkg in results:
            if name == module_name:
                m = import_module("." + name, "src.parser")
                c = getattr(m, class_name)
                return c

    def try_read_text(self, reader) -> str:
        """Try to read text in different encodings."""
        encodings = ["utf-8-sig", "utf-8"]
        for encoding in encodings:
            try:
                # try to read UTF-8-BOM
                return reader.read_text(encoding=encoding)
            except Exception as e:
                print(e)

        raise ValueError("Not able to read the text as any of the encodings.")
