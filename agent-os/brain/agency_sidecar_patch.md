# Agency Sidecar Pattern

When you want to ship a brain image with frozen reference content
(an "agency corpus" — RFCs, agency docs, regulatory text, internal
references) AND let downstream users add their own writable memory
on top, the right shape is **two ChromaDB collections in one
persistent client.**

## The problem

Ship a docker image with a pre-built ChromaDB collection that contains
your foundation corpus. The HNSW segment in that collection is sealed
read-only at image build time (good — index is fast, well-tuned). But
that means every `add()` against that collection silently no-ops:
the call returns success, `count()` never grows. Surprising.

## The fix

In the same `PersistentClient`, lazily create a SECOND collection.
Call it `<image-name>_agency` or `_user`. It is fresh, has a writable
HNSW segment, and accepts writes normally.

In `recall()`, query BOTH collections, merge results by distance,
return top-N to the caller. The user can't tell the difference.

In `remember()`, only ever write to the sidecar.

In `forget()`, only operate on the sidecar (you cannot delete from
the frozen collection regardless).

## Why two collections instead of one writable collection

Because the frozen one is gigabytes (foundation corpus is the
expensive bit) and you do not want to rebuild it on every backup
cycle. With this pattern, `brain-snapshot.ps1` only zips the sidecar
(+ collection-metadata SQLite) — typically a few hundred MB
regardless of how big the foundation is.

## Naming and stable IDs

Use stable document IDs derived from a content hash so re-indexing is
idempotent:

```python
doc_id = sha256(f"{collection_name}:{path}".encode()).hexdigest()[:16]
```

The 16-hex prefix is plenty unique for a per-collection corpus and
keeps the IDs short in logs.

## What about Qdrant / Weaviate / Vespa

Same shape. Two collections / classes / namespaces. Frozen + sidecar.
Merge in the read path. The cost discipline (only back up the
sidecar) is the same.
