from pathlib import Path

from bron.ocr.delpher import pdf_md5
from bron.ocr.sources import is_didl

FIXTURES = Path(__file__).parent.parent / "fixtures" / "ocr" / "delpher"


def test_a_didl_record_passes_and_a_truncated_or_empty_one_does_not() -> None:
    data = (FIXTURES / "didl-3-scans.xml").read_bytes()
    assert is_didl(data)
    assert not is_didl(data[: len(data) // 2])
    assert not is_didl(b"<OAI-PMH><error code='idDoesNotExist'/></OAI-PMH>")


def test_the_volume_pdf_md5_is_read_from_the_didl_record() -> None:
    data = (FIXTURES / "didl-3-scans.xml").read_bytes()
    assert pdf_md5(data) == "c3a8343669a991dd6763e1c7bdbd7e9c"
