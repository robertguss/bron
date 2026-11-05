import pytest

from bron.ocr.pagemap import by_page, page_map, printed_number


@pytest.mark.parametrize(
    ("lines", "expected"),
    [
        (["2 DE ONBEGRIJPELIJKHEID GODS.", "liet begin van haar arbeid"], 2),
        (["DE ONBEGRIJPELIJKHEID GODS. 3", "staat zij voor"], 3),
        (["HET DOGMA.", "§ 26. De namen Gods.", "tekst", "73"], 73),
        (["§ 23. De onbegrijpelijkheid Gods.", "Davidson, Theol."], None),
        (["12 heeren hebben dit gezegd, en meer", "tekst"], None),
        ([], None),
    ],
)
def test_the_printed_number_comes_from_the_running_head_or_the_foot(
    lines: list[str], expected: int | None
) -> None:
    assert printed_number(lines) == expected


def head(n: int) -> list[str]:
    return [f"{n} DE ONBEGRIJPELIJKHEID GODS.", "tekst"]


def test_an_unread_scan_between_agreeing_readings_is_interpolated() -> None:
    texts = [head(1), head(2), ["tekst zonder kop"], head(4), head(5)]
    entries = page_map(texts)
    assert [(e.page, e.method) for e in entries] == [
        (1, "read"),
        (2, "read"),
        (3, "interpolated"),
        (4, "read"),
        (5, "read"),
    ]


def test_a_misreading_no_neighbour_agrees_with_is_set_aside() -> None:
    texts = [head(1), head(2), head(83), head(4), head(5)]
    assert by_page(page_map(texts)) == {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}


def test_a_first_page_that_prints_no_number_is_extrapolated_but_never_below_one() -> None:
    texts = [["Gereformeerde Dogmatiek"], ["§ 23. De onbegrijpelijkheid Gods."], head(2), head(3)]
    entries = page_map(texts)
    assert [(e.page, e.method) for e in entries] == [
        (None, "unresolved"),
        (1, "extrapolated"),
        (2, "read"),
        (3, "read"),
    ]


def test_a_page_number_claimed_twice_is_left_unresolved() -> None:
    texts = [head(1), head(2), head(3), head(3), head(4), head(5), head(6)]
    pages = [e.page for e in page_map(texts)]
    assert 3 not in pages
