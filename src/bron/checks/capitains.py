"""CapiTainS conventions: metadata files, URNs, filenames, and the text's own URN and language.

This reimplements the checklist of CapiTainS' HookTest natively; HookTest itself is
unmaintained and pulls in GPL-licensed MyCapytain.
"""

from collections.abc import Iterator
from pathlib import Path

from lxml import etree

from bron.checks import Context
from bron.findings import Finding
from bron.tei import NSMAP, XML_LANG, tei

CTS_NS = "http://chs.harvard.edu/xmlns/cts"
CTS = {"ti": CTS_NS}
VERSION_KINDS = ("edition", "translation", "commentary")


def check_capitains(context: Context) -> Iterator[Finding]:
    data = context.root / "data"
    if not data.is_dir():
        yield Finding(context.root, None, "cts-layout", "the repository has no data/ directory")
        return
    for textgroup_dir in sorted(p for p in data.iterdir() if p.is_dir()):
        yield from _textgroup(context, textgroup_dir)


def _lang_children(element: etree._Element, name: str) -> list[etree._Element]:
    return [c for c in element.iterfind(f"ti:{name}", CTS) if c.get(XML_LANG)]


def _textgroup(context: Context, folder: Path) -> Iterator[Finding]:
    metadata = folder / "__cts__.xml"
    if not metadata.is_file():
        yield Finding(folder, None, "cts-textgroup", "textgroup directory has no __cts__.xml")
        return
    tree = context.tree(metadata)
    if tree is None:
        yield context.parse_errors[metadata]
        return
    root = tree.getroot()
    urn = root.get("urn", "")
    if root.tag != f"{{{CTS_NS}}}textgroup":
        yield Finding(metadata, root.sourceline, "cts-textgroup", "root must be <ti:textgroup>")
        return
    parts = urn.split(":")
    if len(parts) != 4 or parts[:2] != ["urn", "cts"] or parts[3] != folder.name:
        yield Finding(
            metadata,
            root.sourceline,
            "cts-textgroup",
            f"textgroup urn {urn!r} must be urn:cts:<namespace>:{folder.name}",
        )
    if not _lang_children(root, "groupname"):
        yield Finding(
            metadata, root.sourceline, "cts-textgroup", "needs a <ti:groupname> with xml:lang"
        )
    for work_dir in sorted(p for p in folder.iterdir() if p.is_dir()):
        yield from _work(context, work_dir, urn)


def _work(context: Context, folder: Path, textgroup_urn: str) -> Iterator[Finding]:
    metadata = folder / "__cts__.xml"
    if not metadata.is_file():
        yield Finding(folder, None, "cts-work", "work directory has no __cts__.xml")
        return
    tree = context.tree(metadata)
    if tree is None:
        yield context.parse_errors[metadata]
        return
    work = tree.getroot()
    if work.tag != f"{{{CTS_NS}}}work":
        yield Finding(metadata, work.sourceline, "cts-work", "root must be <ti:work>")
        return
    urn = work.get("urn", "")
    if work.get("groupUrn") != textgroup_urn:
        yield Finding(
            metadata,
            work.sourceline,
            "cts-work",
            f"groupUrn {work.get('groupUrn')!r} must be its textgroup's urn {textgroup_urn!r}",
        )
    if urn != f"{textgroup_urn}.{folder.name}":
        yield Finding(
            metadata,
            work.sourceline,
            "cts-work",
            f"work urn {urn!r} must be {textgroup_urn}.{folder.name}",
        )
    if not work.get(XML_LANG):
        yield Finding(metadata, work.sourceline, "cts-work", "<ti:work> needs xml:lang")
    if not _lang_children(work, "title"):
        yield Finding(metadata, work.sourceline, "cts-work", "needs a <ti:title> with xml:lang")

    listed: set[Path] = set()
    for kind in VERSION_KINDS:
        for version in work.iterfind(f"ti:{kind}", CTS):
            version_urn = version.get("urn", "")
            if version.get("workUrn") != urn:
                yield Finding(
                    metadata,
                    version.sourceline,
                    "cts-edition",
                    f"{kind} {version_urn!r} must have workUrn {urn!r}",
                )
            suffix = version_urn.removeprefix(f"{urn}.")
            if suffix == version_urn or not suffix or "." in suffix:
                yield Finding(
                    metadata,
                    version.sourceline,
                    "cts-edition",
                    f"{kind} urn {version_urn!r} must be {urn}.<version>",
                )
                continue
            if not _lang_children(version, "label"):
                yield Finding(
                    metadata,
                    version.sourceline,
                    "cts-edition",
                    f"{kind} {version_urn} needs a <ti:label> with xml:lang",
                )
            if kind != "edition" and not version.get(XML_LANG):
                yield Finding(
                    metadata,
                    version.sourceline,
                    "cts-edition",
                    f"{kind} {version_urn} needs xml:lang",
                )
            text_path = folder / (version_urn.split(":", 3)[3] + ".xml")
            listed.add(text_path)
            if not text_path.is_file():
                yield Finding(
                    metadata,
                    version.sourceline,
                    "cts-missing-file",
                    f"{kind} {version_urn} is listed but {text_path.name} does not exist",
                )
                continue
            yield from _text(context, text_path, version_urn)

    for xml_file in sorted(folder.glob("*.xml")):
        if xml_file.name != "__cts__.xml" and xml_file not in listed:
            yield Finding(
                xml_file,
                None,
                "cts-unlisted-file",
                f"{xml_file.name} is not listed in its work's __cts__.xml",
            )


def _text(context: Context, path: Path, urn: str) -> Iterator[Finding]:
    tree = context.tree(path)
    if tree is None:
        return  # the schema check reports the parse error
    body = tree.getroot().find(f"{tei('text')}/{tei('body')}")
    if body is None:
        yield Finding(path, None, "cts-body-urn", "the text has no <text>/<body>")
        return
    if body.get("n") != urn:
        yield Finding(
            path,
            body.sourceline,
            "cts-body-urn",
            f"body/@n is {body.get('n')!r} but the file and its metadata name {urn!r}",
        )
    if not body.get(XML_LANG):
        yield Finding(path, body.sourceline, "cts-body-lang", "<body> needs xml:lang")
    patterns = tree.xpath(
        "/tei:TEI/tei:teiHeader/tei:encodingDesc/tei:refsDecl[@n='CTS']/tei:cRefPattern",
        namespaces=NSMAP,
    )
    if not patterns:
        yield Finding(
            path,
            None,
            "cts-citation",
            'the header needs <refsDecl n="CTS"> with one cRefPattern per citation level',
        )
