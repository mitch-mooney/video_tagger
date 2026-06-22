# ADR 0001 — `core/` may import `data/` for persistence orchestration

- Status: accepted
- Date: 2026-06-22

## Context

Introducing the **Project document** (`core/project_document.py`) — the central live editing
object — gives it ownership of `save()`/`save_as()`. Saving delegates bytes to
`ProjectManager` (`data/project_manager.py`). Today `core/` imports only `models/`, so this
adds a new `core → data` import edge.

## Decision

`core/` may import `data/` **for persistence orchestration only**. The Project document
holds the file path and dirty flag and calls `ProjectManager.save/load`; `ProjectManager`
stays a leaf that knows the on-disk format. The reverse edge (`data → core`) remains
forbidden.

## Consequences

- The Project document is the app's central object and a reasonable place to own "save".
- `ProjectManager` stays a persistence leaf; the on-disk format is consolidated there (see
  the planned persistence-seam work).
- Callers depend on the document's stable `save()`/`save_as()` interface, insulated from
  future changes to the persistence format.
- Do not re-suggest "move persistence out of core" in architecture reviews — this edge is
  intentional and scoped to persistence.
