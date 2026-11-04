from pathlib import Path

import pytest

from bron.convert.gd1.pagemap import (
    MAP,
    VOLUMES,
    HashMismatch,
    Review,
    Volume,
    load_map,
    measure,
    printed_number,
    reviews_of,
    verified_pdf,
)

OCR = Path(__file__).parents[1] / "fixtures" / "gd1" / "ocr"


def ocr_pages(volume: int, first: int, last: int) -> dict[int, list[str]]:
    """Fixture OCR lines of the PDF pages first..last that have a fixture, by 1-based page."""
    pages = {}
    for index in range(first, last + 1):
        path = OCR / f"vol{volume}-pdf{index:03d}.txt"
        if path.is_file():
            lines = path.read_text(encoding="utf-8").splitlines()
            pages[index] = [line for line in lines if line.strip()]
    return pages


def pdf_of(pages: dict[int, list[str]], count: int) -> list[list[str]]:
    """A whole PDF's lines: the given pages, and blank pages everywhere else."""
    return [pages.get(index, []) for index in range(1, count + 1)]


VOL1_START = Volume(number=1, roman=("III", "IV", "V", "VI", "VII"), last_page=17)


def entries(result, volume=1):
    return {entry.n: entry for entry in result.volumes[volume]}


def test_header_number_maps_printed_15_to_pdf_25_by_ocr() -> None:
    result = measure({1: pdf_of(ocr_pages(1, 23, 27), 30)}, {1: Volume(1, (), 17)}, [])
    page = entries(result)["15"]
    assert (page.pdf, page.method) == (25, "ocr")
    assert "header" in page.evidence


def test_roman_running_heads_are_read_on_either_side() -> None:
    assert printed_number(["IV VOORBERICHT.", "Thomas"], roman=True) == ("IV", "header")
    assert printed_number(["VOORBERICHT. V", "het"], roman=True) == ("V", "header")
    assert printed_number(["INHOUD.\tVII", "x"], roman=True) == ("VII", "header")


def test_roman_numerals_are_not_read_in_volumes_without_roman_pages() -> None:
    assert printed_number(["I 76, II 30, III 20. Melius", "x"], roman=False) is None


def test_a_number_in_the_footer_line_counts_when_the_header_has_none() -> None:
    assert printed_number(["HOOFDSTUK VI.", "Over de wereld", "1"], roman=False) == (
        "1",
        "footer",
    )


def test_a_page_with_no_readable_number_between_matches_is_interpolated_and_listed() -> None:
    # PDF 8 is the unnumbered first page of the contents, between V (7) and VII (9).
    result = measure({1: pdf_of(ocr_pages(1, 5, 27), 30)}, {1: VOL1_START}, [])
    page = entries(result)["VI"]
    assert (page.pdf, page.method) == (8, "interpolated")
    assert (1, "VI") in result.interpolated


def test_pages_outside_any_bracket_stay_unresolved_until_reviewed() -> None:
    result = measure({1: pdf_of(ocr_pages(1, 5, 27), 30)}, {1: VOL1_START}, [])
    assert {(1, "III"), (1, "1"), (1, "2")} <= set(result.unresolved)
    assert not result.complete


def test_a_review_resolves_a_page_and_marks_it_visually_verified() -> None:
    reviews = [
        Review(1, "III", 5, "Voorbericht opens; unnumbered."),
        Review(1, "1", 11, "Inleiding opens; unnumbered."),
        Review(1, "2", 12, "Header misread as ON."),
    ]
    result = measure({1: pdf_of(ocr_pages(1, 5, 27), 30)}, {1: VOL1_START}, reviews)
    page = entries(result)["1"]
    assert (page.pdf, page.method, page.note) == (
        11,
        "visually verified",
        "Inleiding opens; unnumbered.",
    )
    assert result.unresolved == []


def test_two_matches_that_disagree_with_their_pdf_order_are_a_conflict() -> None:
    # An unnumbered plate after printed 14 pushes 15 to 17 one PDF page later.
    pages = {23: ["13", "text"], 24: ["14", "text"], 26: ["15", "text"], 27: ["16", "text"]}
    pages[28] = ["17", "text"]
    result = measure({1: pdf_of(pages, 30)}, {1: Volume(1, (), 17)}, [])
    assert result.conflicts, "a change of offset between neighbours must be reported"
    assert not result.complete


def test_a_lone_misread_number_is_reported_as_an_outlier_not_used() -> None:
    pages = ocr_pages(1, 23, 27)
    pages[24] = ["11", *pages[24][1:]]  # "14" misread as "11"
    result = measure({1: pdf_of(pages, 30)}, {1: Volume(1, (), 17)}, [])
    assert (1, 24, "11") in result.outliers
    page = entries(result)["14"]
    assert (page.pdf, page.method) == (24, "interpolated")


def test_a_review_that_contradicts_an_ocr_match_is_a_conflict() -> None:
    reviews = [Review(1, "15", 26, "wrong")]
    result = measure({1: pdf_of(ocr_pages(1, 23, 27), 30)}, {1: Volume(1, (), 17)}, reviews)
    assert any("15" in conflict for conflict in result.conflicts)


def test_a_pdf_whose_hash_differs_from_the_registry_fails_before_matching(
    tmp_path: Path,
) -> None:
    pdf = tmp_path / "scan.pdf"
    pdf.write_bytes(b"%PDF-1.4 not the registered file")
    with pytest.raises(HashMismatch):
        verified_pdf(pdf, "0" * 64)


def test_the_shipped_map_lists_every_printed_page_once_and_resolves_each() -> None:
    page_map = load_map(MAP)
    reviewed = {(review.volume, review.n) for review in reviews_of(page_map)}
    for volume in page_map["volumes"]:
        pages = volume["pages"]
        assert [page["n"] for page in pages] == list(VOLUMES[volume["volume"]].labels)
        for page in pages:
            assert isinstance(page["pdf"], int), (volume["volume"], page)
            reviewed_here = (volume["volume"], page["n"]) in reviewed
            assert (page["method"] == "visually verified") == reviewed_here
