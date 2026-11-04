"""The two printings' source copies, as bron-data's registry records them, and their cache.

The second printing is Delpher's VU copy, one registry record per volume
(`gd2-vol<n>-delpher`). The fourth printing is the theologienet PDFs
(`gd2-vol<n>-theologienet`). The cache keeps each fetched object in its own directory:
`delpher/<id>-didl`, `delpher/<id>-pdf`, `delpher/<scan>-image`, `delpher/<scan>-alto`
and `theologienet/gd-<roman>`.
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from bron.ocr import OcrError, delpher
from bron.ocr.download import Downloader

VOLUMES = (1, 2, 3, 4)
SPACING = {
    "resolver.kb.nl": 10.0,
    "services.kb.nl": 10.0,
    "www.delpher.nl": 10.0,
    "theologienet.nl": 120.0,
}


def load_registry(path: Path) -> dict[str, Mapping[str, Any]]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return {record["id"]: record for record in data["sources"]}


def record(registry: Mapping[str, Mapping[str, Any]], volume: int, kind: str) -> Mapping[str, Any]:
    wanted = f"gd2-vol{volume}-{kind}"
    if wanted not in registry:
        raise OcrError(f"the registry has no source {wanted!r}")
    return registry[wanted]


def key(identifier: str) -> str:
    return identifier.replace(":", "_")


def didl(downloader: Downloader, volume_id: str) -> Path:
    return downloader.fetch(
        "delpher", f"{key(volume_id)}-didl", delpher.didl_url(volume_id), "didl.xml"
    )


def volume_pdf(downloader: Downloader, volume_id: str) -> Path:
    return downloader.fetch(
        "delpher", f"{key(volume_id)}-pdf", delpher.pdf_url(volume_id), "volume.pdf"
    )


def scan_image(downloader: Downloader, scan: delpher.Scan) -> Path:
    return downloader.fetch(
        "delpher",
        f"{key(scan.identifier)}-image",
        scan.image_url,
        "image.jp2",
        md5sum=scan.image_md5,
    )


def scan_alto(downloader: Downloader, scan: delpher.Scan) -> Path:
    return downloader.fetch(
        "delpher", f"{key(scan.identifier)}-alto", scan.alto_url, "alto.xml", md5sum=scan.alto_md5
    )


def theologienet_pdf(downloader: Downloader, source: Mapping[str, Any]) -> Path:
    filename = str(source["holder_id"])
    roman = filename.removesuffix(".pdf").rsplit("-", 1)[-1]
    return downloader.fetch(
        "theologienet", f"gd-{roman}", source["url"], filename, sha256sum=source["sha256"]
    )
