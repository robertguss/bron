"""Conversion of the first edition of Bavinck's Gereformeerde Dogmatiek (GD¹) to TEI.

`bron convert gd1` turns the four Distributed Proofreaders transcriptions on Project
Gutenberg into one TEI file, once. The modules follow the steps: `fetch` gets each volume
as registered, `html` reads it and maps its inline markup, `regions` splits it into front
matter, body and back matter, `structure` builds chapters, sections and subparagraphs,
`pages`, `notes` and `corrections` encode page breaks, footnotes and the transcribers'
corrections, `header` writes the TEI header, and `emit` assembles and serializes the file.
"""


class ConversionError(Exception):
    """The source cannot be converted as it stands; the message says where."""
