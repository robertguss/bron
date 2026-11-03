# Bron's DTS resolver

`bron serve <data-repo> --base-url <url> --port <n>` answers DTS 1.0 requests for a
CapiTainS data repository. It reads the repository once at startup into an in-memory
index and serves from that. It has no database, writes nothing, and needs nothing but the
data repository. It refuses to start when the repository cannot be indexed; `bron check`
names the underlying problems.

## Endpoints

| Endpoint | URI template |
|---|---|
| Entry | `{base}/` |
| Collection | `{base}/collection{?id,page,nav}` |
| Navigation | `{base}/navigation{?resource,ref,start,end,down,tree,page}` |
| Document | `{base}/document{?resource,ref,start,end,tree,mediaType}` |

- **Identifiers.** Collection and resource ids are CTS URNs. The root collection is
  `urn:cts:<namespace>`, its members are the textgroups, then works, then each work's
  editions, translations and commentaries as Resources.
- **Order.** Navigation members are in document order, so `3.10` follows `3.9`.
- **Citation trees.** Each text has one citation tree, read from its default
  `citeStructure`. A request may name it `tree=default` or leave `tree` out. Any other
  tree is 404.
- **Navigation.** Every combination in the specification's table, including `start` and
  `end`. A `down` deeper than the tree returns what exists. A range with `down` lists the
  units from `start` through the whole of `end`, from the shallower of their levels to
  `down` levels below the deeper.
- **Document.** Without `ref` or `start`/`end`, the whole TEI file. With them, a TEI
  document whose `<dts:wrapper>` holds the cited units in document order. A range holds
  the fewest whole units, at the shallower of the two cited levels or below, that cover
  `start` through `end`. So a range of subparagraphs that crosses a section boundary holds
  the subparagraphs on each side, never the sections that contain them.
  `mediaType` other than `application/tei+xml` is 404. Responses carry `Link: <{base}/collection?id=<urn>>; rel="collection"`.
- **Page anchor.** Each fragment opens with the page break it begins on: the last `<pb>`
  at or before its start. When the fragment's own first content is a `<pb>`, that one
  serves. Otherwise a copy is added without its `xml:id` and with `corresp` pointing at the
  original, so a fragment never holds an identifier twice.
- **Pagination.** Responses are never paginated. `page=1` is accepted; any other page
  is 404.
- **Media types.** Entry, Collection and Navigation answer `application/ld+json`.
  Document answers `application/tei+xml`.

## Redirected and retired identifiers

The DTS specification does not cover identifiers that have been withdrawn. Bron records
them in the data repository's `identifiers/redirects.yaml`, and the resolver answers a
Navigation or Document request naming one in `ref`, `start` or `end` like this:

| The identifier is | Answer |
|---|---|
| redirected to one replacement | `301`, `Location` is the same request with the replacement in its place |
| redirected to several (a split) | `300`, a problem body listing each replacement's URN and request URL |
| retired | `410`, a tombstone problem body: URN, reason and date |

A replacement that was itself redirected answers in turn, so a client following
redirects reaches a live identifier.

## Errors

Every error answers with an [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem
body, `application/problem+json`:

```json
{"type": "about:blank", "title": "Not Found", "status": 404, "detail": "..."}
```

The `300` and `410` bodies add `urn`, `reason` and `date`, and the `300` body adds
`replaced_by`, a list of `{"urn": ..., "url": ...}`.

- **400** for the specification's invalid combinations: no `resource`; `ref` with `start`
  or `end`; `start` without `end` or the reverse; Navigation with neither `ref`, a range
  nor `down`; `down=0` without `ref`; a `down` below `-1`; a parameter of the wrong type;
  `start` after `end`; `nav` other than `children` or `parents`.
- **404** for an unknown collection, resource, ref or tree, an unavailable `mediaType`,
  or a page other than 1.
