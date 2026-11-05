import pytest

from bron.ocr import OcrError
from bron.ocr.sample import (
    Draw,
    Judgment,
    NeedJudgments,
    orders,
    seed_from_commit,
    select,
    slice_pages,
)

COMMIT = "0738b7815291f93af6d8af610bc207ac3361a6e5"
NONE = Judgment(greek=False, hebrew=False)
GREEK = Judgment(greek=True, hebrew=False)
HEBREW = Judgment(greek=False, hebrew=True)
BOTH = Judgment(greek=True, hebrew=True)


def population() -> dict[int, list[int]]:
    return {
        1: list(range(1, 501)),
        2: list(range(1, 501)),
        3: list(range(1, 501)),
        4: list(range(1, 501)),
    }


def test_the_seed_is_the_commit_read_as_a_number() -> None:
    assert seed_from_commit(COMMIT) == int(COMMIT, 16)
    with pytest.raises(OcrError, match="40-character"):
        seed_from_commit("0738b78")


def test_the_slice_runs_from_par_23_to_the_page_before_par_26_begins() -> None:
    texts = [
        ["front"],
        ["§ 23. De onbegrijpelijkheid Gods."],
        ["2 KOP"],
        ["3 KOP"],
        ["4 KOP", "§ 26. De namen Gods."],
        ["5 KOP"],
    ]
    scan_to_page = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5}
    assert slice_pages(texts, scan_to_page) == [1, 2, 3]


def test_the_same_seed_always_draws_the_same_pages_and_another_seed_others() -> None:
    first = orders(seed_from_commit(COMMIT), population(), list(range(1, 74)))
    again = orders(seed_from_commit(COMMIT), population(), list(range(1, 74)))
    other = orders(seed_from_commit("1" * 40), population(), list(range(1, 74)))
    assert (first.slice, first.orders) == (again.slice, again.orders)
    assert first.slice != other.slice
    assert len(first.slice) == 4 and all(1 <= p <= 73 for p in first.slice)


def judged(draw: Draw, overrides: dict[tuple[int, int], Judgment]) -> dict:
    """Every page in every order judged as carrying neither script, except the overrides."""
    judgments = {(v, p): NONE for v, order in draw.orders.items() for p in order}
    judgments.update(overrides)
    return judgments


def test_the_first_picks_must_be_judged_before_anything_is_chosen() -> None:
    draw = orders(1, population(), list(range(1, 74)))
    result = select(draw, {})
    assert isinstance(result, NeedJudgments)
    assert result.pages == tuple((v, p) for v in (1, 3, 4) for p in draw.orders[v][:2])


def test_six_picks_carrying_both_scripts_are_kept_as_drawn() -> None:
    draw = orders(1, population(), list(range(1, 74)))
    picks = {v: draw.orders[v][:2] for v in (1, 3, 4)}
    result = select(draw, judged(draw, {(1, picks[1][0]): GREEK, (4, picks[4][1]): HEBREW}))
    assert isinstance(result, Draw)
    assert result.picks == picks and result.replacements == []


def test_a_missing_script_replaces_the_second_pick_of_the_earliest_qualifying_volume() -> None:
    draw = orders(1, population(), list(range(1, 74)))
    greek_page = draw.orders[3][5]
    result = select(draw, judged(draw, {(3, greek_page): GREEK, (1, draw.orders[1][0]): HEBREW}))
    assert isinstance(result, Draw)
    assert result.picks[3] == [draw.orders[3][0], greek_page]
    assert result.replacements == [
        {"script": "greek", "volume": 3, "replaced": draw.orders[3][1], "by": greek_page, "pick": 2}
    ]


def test_both_scripts_missing_with_vol_1_qualifying_for_both_fill_its_two_picks() -> None:
    draw = orders(1, population(), list(range(1, 74)))
    greek_page, hebrew_page = draw.orders[1][4], draw.orders[1][9]
    judgments = judged(draw, {(1, greek_page): GREEK, (1, hebrew_page): HEBREW})
    result = select(draw, judgments)
    assert isinstance(result, Draw)
    assert result.picks[1] == [hebrew_page, greek_page]
    assert select(draw, judgments) == result


def test_the_only_page_carrying_the_other_script_is_never_replaced() -> None:
    draw = orders(1, population(), list(range(1, 74)))
    greek_page = draw.orders[1][7]
    judgments = judged(draw, {(1, draw.orders[1][1]): HEBREW, (1, greek_page): GREEK})
    result = select(draw, judgments)
    assert isinstance(result, Draw)
    assert result.picks[1] == [greek_page, draw.orders[1][1]]


def test_an_unjudged_candidate_on_the_way_to_a_qualifying_page_is_asked_for() -> None:
    draw = orders(1, population(), list(range(1, 74)))
    judgments = {(v, p): NONE for v in (1, 3, 4) for p in draw.orders[v][:2]}
    judgments[(1, draw.orders[1][0])] = HEBREW
    result = select(draw, judgments)
    assert isinstance(result, NeedJudgments)
    assert result.pages[0] == (1, draw.orders[1][2])
    assert len(result.pages) == 10


def test_a_script_no_page_carries_is_reported_missing() -> None:
    draw = orders(1, population(), list(range(1, 74)))
    result = select(
        draw,
        judged(draw, {(1, draw.orders[1][0]): BOTH})
        | {(v, p): NONE for v in (3, 4) for p in draw.orders[v]},
    )
    assert isinstance(result, Draw) and result.missing_scripts == []
    result = select(draw, judged(draw, {(1, draw.orders[1][0]): GREEK}))
    assert isinstance(result, Draw) and result.missing_scripts == ["hebrew"]
