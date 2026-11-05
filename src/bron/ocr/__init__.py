"""The GD² OCR sample test: sources, sample, engines, ground truth and scores.

`bron ocr` draws a seeded sample of second-printing pages, fetches their scans and the
libraries' own OCR, finds the same words in the fourth printing, and prepares the reader's
packets. The modules follow those steps: `download` fetches politely into a cache,
`delpher` and `pdfsource` read the two printings' sources, `sample` draws the pages,
`spans` matches them in the fourth printing, `manifest` records everything with its
hashes, and `packets` builds what the reader receives.
"""


class OcrError(Exception):
    """A source, sample or packet is not as the protocol requires; the message says how."""
