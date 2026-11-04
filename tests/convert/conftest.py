from collections.abc import Callable
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from lxml import etree

from bron.convert.gd1.emit import Volume, convert_volume
from bron.convert.gd1.pagemap import MAP, load_map
from bron.tei import NSMAP

GD1 = Path(__file__).parents[1] / "fixtures" / "gd1"
PAGE_MAP = load_map(MAP)


def excerpt(volume: int) -> bytes:
    """A trimmed real excerpt of one volume's Gutenberg HTML."""
    return (GD1 / f"vol{volume}.html").read_bytes()


def edited(volume: int, old: str, new: str) -> bytes:
    """The excerpt with exactly one occurrence of `old` replaced by `new`."""
    text = excerpt(volume).decode("utf-8")
    assert text.count(old) == 1, f"expected one {old!r} in vol{volume}.html"
    return text.replace(old, new).encode("utf-8")


def registry() -> dict:
    return yaml.safe_load((GD1 / "sources.yaml").read_text(encoding="utf-8"))


def xpath(node: etree._Element, path: str) -> list:
    return node.xpath(path, namespaces=NSMAP)


def text_of(node: etree._Element) -> str:
    return " ".join("".join(node.itertext()).split())


@pytest.fixture(scope="session")
def converted() -> Callable[[int], Volume]:
    """Each volume's excerpt, converted once per test session."""
    cache: dict[int, Volume] = {}

    def get(volume: int) -> Volume:
        if volume not in cache:
            cache[volume] = convert_volume(excerpt(volume), volume, PAGE_MAP)
        return cache[volume]

    return get


def wrap(elements: list[etree._Element]) -> etree._Element:
    """Elements under one TEI parent, so XPath can run over a volume's region."""
    parent = etree.Element("{http://www.tei-c.org/ns/1.0}div")
    parent.extend(deepcopy(element) for element in elements)
    return parent
