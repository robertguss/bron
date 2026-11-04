from bron.ocr.delpher import AltoLine
from bron.ocr.pdfsource import Half, Spreads
from bron.ocr.spans import Haystack, locate, parts

BODY_SIZE, NOTE_SIZE = 10.0, 8.0


def line(text: str, y: int, size: float = BODY_SIZE) -> AltoLine:
    return AltoLine(text, (300, y, 1300, 30), size)


def sampled_page(body: list[str], notes: tuple[str, ...] = ()) -> list[AltoLine]:
    lines = [line("2 DE ONBEGRIJPELIJKHEID GODS.", 170)]
    lines += [line(text, 260 + 40 * i) for i, text in enumerate(body)]
    lines += [line(text, 2400 + 30 * i, NOTE_SIZE) for i, text in enumerate(notes)]
    return lines


FILLER = "en de kerk heeft dit altijd beleden tegenover allerlei dwaling in alle eeuwen " * 3


def spreads(pages: dict[int, str]) -> Spreads:
    halves = []
    for i, (n, text) in enumerate(sorted(pages.items())):
        head = f"{n} DE KENBAARHEID GODS" if n % 2 == 0 else f"DE KENBAARHEID GODS {n}"
        halves.append(Half(i // 2, i % 2, (head, *text.split("\n"))))
    return Spreads(tuple(halves), tuple(0 for _ in halves), tuple(1.0 for _ in halves))


OPENING = "maar ook in de verdere loop als ze"
CLOSING = "het zelfbewustzijn der godheid zelve uitspreekt"


def test_a_page_reprinted_within_one_page_is_found_on_it() -> None:
    page = sampled_page([OPENING + " de leer van God ontwikkelt", FILLER, "waarin zij " + CLOSING])
    hay = Haystack.build(
        spreads(
            {
                10: FILLER,
                11: FILLER,
                12: OPENING + " de leer van God ontwikkelt " + FILLER + " waarin zij " + CLOSING,
                13: FILLER,
                14: FILLER,
            }
        )
    )
    found = locate(page, 12, 1.0, hay)
    assert found["covering_pages"] == [12]
    assert found["opening"]["score"] >= 95 and not found["opening"]["ambiguous"]


def test_a_page_whose_words_cross_a_page_break_covers_both_pages() -> None:
    page = sampled_page([OPENING + " de leer van God ontwikkelt", FILLER, "waarin zij " + CLOSING])
    hay = Haystack.build(
        spreads(
            {
                10: FILLER,
                11: FILLER,
                12: OPENING + " de leer",
                13: "van God ontwikkelt " + FILLER + " waarin zij " + CLOSING,
                14: FILLER,
            }
        )
    )
    assert locate(page, 12, 1.0, hay)["covering_pages"] == [12, 13]


def test_opening_words_with_two_ocr_errors_are_still_found() -> None:
    page = sampled_page([OPENING + " de leer van God ontwikkelt", FILLER, "waarin zij " + CLOSING])
    garbled = "rnaar ook in de verdere 1oop als ze de leer van God ontwikkelt"
    hay = Haystack.build(
        spreads({11: FILLER, 12: garbled + FILLER + " waarin zij " + CLOSING, 13: FILLER})
    )
    assert locate(page, 12, 1.0, hay)["opening"]["page"] == 12


def test_words_printed_twice_in_the_window_are_reported_ambiguous() -> None:
    page = sampled_page([OPENING + " de leer van God ontwikkelt", FILLER, "waarin zij " + CLOSING])
    text = OPENING + " de leer van God ontwikkelt " + FILLER + " waarin zij " + CLOSING
    hay = Haystack.build(spreads({11: text, 12: FILLER, 13: text}))
    assert locate(page, 12, 1.0, hay)["opening"]["ambiguous"] is True


def test_a_footnote_printed_on_the_next_page_is_listed_with_that_page() -> None:
    note = "1) Augustinus de doctrina christiana boek een hoofdstuk zes"
    page = sampled_page(
        [OPENING + " de leer van God ontwikkelt", FILLER, "waarin zij " + CLOSING], (note,)
    )
    hay = Haystack.build(
        spreads(
            {
                11: FILLER,
                12: OPENING + " de leer van God ontwikkelt " + FILLER + " waarin zij " + CLOSING,
                13: FILLER + " " + note,
                14: FILLER,
            }
        )
    )
    found = locate(page, 12, 1.0, hay)
    assert [n["page"] for n in found["notes"]] == [13]


def test_the_running_head_body_and_notes_are_told_apart() -> None:
    split = parts(sampled_page(["regel een", "regel twee"], ("1) een noot",)))
    assert [x.text for x in split.head] == ["2 DE ONBEGRIJPELIJKHEID GODS."]
    assert [x.text for x in split.body] == ["regel een", "regel twee"]
    assert [x.text for x in split.notes] == ["1) een noot"]


def test_a_running_head_with_a_stray_mark_is_still_the_head_given_the_page() -> None:
    lines = [line("■556 DE HEILSORDE.", 170), line("regel een", 260), line("regel twee", 300)]
    assert [x.text for x in parts(lines, 556).head] == ["■556 DE HEILSORDE."]
    assert parts(lines).head == ()


def test_a_heading_without_the_page_number_stays_in_the_body() -> None:
    lines = [line("§ 30. DE NAMEN GODS.", 170), line("regel een", 260)]
    assert parts(lines, 556).head == ()


def test_a_footnote_cited_again_far_off_is_found_with_its_body() -> None:
    note = "1) Calvijn Inst IV 14 13 en verder Beza"
    page = sampled_page(
        [OPENING + " de leer van God ontwikkelt", FILLER, "waarin zij " + CLOSING], (note,)
    )
    body = OPENING + " de leer van God ontwikkelt " + FILLER + " waarin zij " + CLOSING
    hay = Haystack.build(
        spreads({11: FILLER, 12: body + " " + note, 13: FILLER, 30: FILLER + " " + note})
    )
    found = locate(page, 30, 1.0, hay)
    assert found["covering_pages"] == [12]
    assert [(n["page"], n["ambiguous"]) for n in found["notes"]] == [(12, False)]
