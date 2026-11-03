"""The TEI Schematron constraints that apply to the elements Bron's files use.

tei_all's embedded Schematron needs an XSLT 2 pipeline that neither lxml nor jing runs, so
the rules that bind Bron's encodings are enforced here. `src/bron/schemas/README.md` lists
which rules are enforced and why the rest do not apply.
"""

from collections.abc import Iterator

from bron.checks import Context
from bron.findings import Finding
from bron.tei import NSMAP

# Bron's one documented deviation: an insertion or deletion points at the unit that exists on
# one side only, so these link types carry exactly one target (ADR 0017).
ONE_TARGET_LINK_TYPES = frozenset({"insert", "delete"})


def check_tei_constraints(context: Context) -> Iterator[Finding]:
    for path in context.tei_files():
        tree = context.tree(path)
        if tree is None:
            continue

        for link in tree.iterfind(".//tei:link", NSMAP):
            targets = link.get("target", "").split()
            if link.get("type") in ONE_TARGET_LINK_TYPES:
                if len(targets) != 1:
                    yield Finding(
                        path,
                        link.sourceline,
                        "tei-link-targets",
                        f"a {link.get('type')} link must have exactly one target "
                        f"(Bron's documented deviation), not {len(targets)}",
                    )
            elif len(targets) < 2:
                yield Finding(
                    path,
                    link.sourceline,
                    "tei-link-targets",
                    "a link must have at least two targets",
                )

        for structure in tree.iterfind(".//tei:citeStructure", NSMAP):
            parent = structure.getparent()
            nested = parent is not None and parent.tag == structure.tag
            absolute = structure.get("match", "").startswith("/")
            if nested and absolute:
                yield Finding(
                    path,
                    structure.sourceline,
                    "tei-citestructure-match",
                    "a nested citeStructure @match must not start with '/'",
                )
            elif not nested and not absolute:
                yield Finding(
                    path,
                    structure.sourceline,
                    "tei-citestructure-match",
                    "the outer citeStructure @match must start with '/'",
                )

        for element in tree.xpath("//tei:*[@subtype][not(@type)]", namespaces=NSMAP):
            yield Finding(path, element.sourceline, "tei-subtype", "@subtype is used without @type")

        for element in tree.xpath(
            "//tei:p[ancestor::tei:p or ancestor::tei:ab][not(ancestor::tei:floatingText"
            " | parent::tei:exemplum | parent::tei:item | parent::tei:note | parent::tei:q"
            " | parent::tei:quote | parent::tei:remarks | parent::tei:said | parent::tei:sp"
            " | parent::tei:stage | parent::tei:cell | parent::tei:figure)]"
            " | //tei:div[ancestor::tei:p or ancestor::tei:ab][not(ancestor::tei:floatingText)]",
            namespaces=NSMAP,
        ):
            yield Finding(
                path,
                element.sourceline,
                "tei-abstract-model",
                f"<{element.xpath('local-name()')}> may not occur inside <p> or <ab>",
            )

        for element in tree.xpath(
            "//tei:ref[@target and @cRef] | //tei:ptr[@target and @cRef]", namespaces=NSMAP
        ):
            yield Finding(
                path, element.sourceline, "tei-pointer", "@target and @cRef are both supplied"
            )

        for element in tree.xpath("//tei:s[tei:s]", namespaces=NSMAP):
            yield Finding(path, element.sourceline, "tei-s-nesting", "<s> contains another <s>")
