"""TEI helpers shared by the checks, the resolver and the converters."""

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NSMAP = {"tei": TEI_NS}

XML_LANG = f"{{{XML_NS}}}lang"
XML_ID = f"{{{XML_NS}}}id"
XML_BASE = f"{{{XML_NS}}}base"


# The CapiTainS citation declaration in a TEI header.
CTS_REFSDECL = "/tei:TEI/tei:teiHeader/tei:encodingDesc/tei:refsDecl[@n='CTS']"


def xml_ids(tree) -> set[str]:
    """Every xml:id in a parsed document."""
    return {value for element in tree.iter() if (value := element.get(XML_ID))}


def tei(local: str) -> str:
    """Clark-notation name of a TEI element."""
    return f"{{{TEI_NS}}}{local}"
