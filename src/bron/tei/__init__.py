"""TEI helpers shared by the checks, the resolver and the converters."""

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NSMAP = {"tei": TEI_NS}

XML_LANG = f"{{{XML_NS}}}lang"
XML_ID = f"{{{XML_NS}}}id"
XML_BASE = f"{{{XML_NS}}}base"


def tei(local: str) -> str:
    """Clark-notation name of a TEI element."""
    return f"{{{TEI_NS}}}{local}"
