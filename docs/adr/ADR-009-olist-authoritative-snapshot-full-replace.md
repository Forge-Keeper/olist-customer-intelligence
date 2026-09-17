# ADR-009 — Use Protected FULL_REPLACE for Authoritative Olist Snapshots

- **Status:** Proposed
- **Date:** 2026-09-17
- **Decision owners:** Project maintainers
- **Scope:** Olist static CSV snapshot persistence in Bronze and deterministic Olist Silver snapshot outputs

## Context

The public Olist datasets used by this repository are distributed as complete CSV files rather than as an event stream, CDC feed, incremental export, or bounded change set.

The current Olist Bronze ingestion path models those files as authoritative snapshots. The repository already declares `WriteStrategy.FULL_REPLACE` for the current Olist CSV Bronze contracts, including Customers, Sellers, Marketing Qualified Leads, Closed Deals, Products, Product Category Translation, Geolocation, Orders, Order Items, Order Payments, and Order Reviews.

The currently delivered Olist Silver datasets — Customers, Orders, Product Category Translation, Products, Sellers, and Order Items — are also rebuilt from the accepted complete Bronze snapshot and persisted as deterministic full-snapshot outputs.

This behavior is already implemented and runtime-tested, but its rationale was distributed across feature documents and individual dataset contracts. Older repository guidance also stated that complete overwrite should not be used when selective `replaceWhere` is viable. That rule is correct for bounded reprocessing, but it is incomplete for authoritative static snapshots: replacing the full target is the intended normal-write semantics when the input represents the complete current dataset universe.

A durable decision is required so future changes do not accidentally:

- replace snapshot semantics with row-by-row `MERGE` merely because a logical key exists;
- retain rows that disappeared from a later authoritative snapshot;
- invent a key for naturally keyless source data such as Olist Geolocation;
- confuse normal snapshot persistence with bounded replay/reprocessing;
- generalize `FULL_REPLACE` to sources that deliver only partial state.

## Decision

### 1. Authoritative Olist CSV snapshots use FULL_REPLACE as their normal write strategy

When an Olist source file represents the complete authoritative snapshot for that dataset version, the persisted target is replaced as a whole after validation.

For Bronze, this is expressed through:

```text
DatasetContract.write_strategy = FULL_REPLACE
```

The write is not an incremental upsert. Rows absent from the accepted snapshot must not survive merely because they existed in a previous target state.

### 2. FULL_REPLACE is a semantic decision, not a convenience shortcut

Use `FULL_REPLACE` only when all of the following are true:

1. the input scope is known to represent the complete authoritative dataset state for the target;
2. partial delivery is not being interpreted as a complete snapshot;
3. the persisted schema is explicit through `DatasetContract`;
4. blocking validation completes before destructive replacement;
5. an unexpectedly empty snapshot is rejected before overwrite;
6. rerunning the same accepted business state produces the same business rows and keys, excluding expected operational timestamps.

A logical primary key does not by itself imply that `MERGE` is preferable. For a complete snapshot, `MERGE` would preserve stale target rows unless explicit delete semantics were added. Full replacement directly matches the source contract.

### 3. Protected replacement is mandatory

A full replacement must fail closed.

For the current Bronze path:

```text
source snapshot
  -> source/schema validation
  -> Data Quality when configured
  -> runtime DatasetContract type validation
  -> non-empty snapshot guard
  -> Delta lifecycle compatibility
  -> overwrite complete target
```

For the current Silver path:

```text
accepted Bronze snapshot
  -> explicit typed transformation
  -> blocking/referential Data Quality
  -> persist DQ evidence
  -> reject on blocking failure
  -> non-empty snapshot guard
  -> Delta lifecycle compatibility
  -> overwrite complete Silver target
```

Blocking validation failures must preserve the previous target state.

### 4. Empty authoritative snapshots are rejected by default

The current Olist snapshot contracts do not treat an empty file as a legitimate complete dataset state.

`BronzeWriter` therefore rejects an empty `FULL_REPLACE` batch before table lifecycle/write execution. Current Silver snapshot processors apply the same fail-closed principle before replacement.

If a future dataset can legitimately become empty, that requires an explicit contract change and supporting evidence. It must not be enabled by weakening the generic safety guard silently.

### 5. MERGE remains the normal strategy for keyed partial-state ingestion

`MERGE` remains appropriate when an incoming batch represents keyed rows to insert/update but does **not** represent the complete target universe.

Examples in the current architecture include API ingestion paths where repeated ingestion of the same logical key is expected to update/insert that key without deleting unrelated target rows.

A source being keyed is insufficient justification for `MERGE`; batch completeness and source semantics decide the strategy.

### 6. replaceWhere remains the explicit bounded-reprocessing strategy

`replaceWhere` is used when the caller explicitly identifies a bounded target scope to rebuild, such as a date range or date-plus-business-key interval.

It is not an implicit normal-write fallback.

Current examples include:

- Weather reprocessing bounded by coordinates plus date interval;
- ANP bounded date-interval replacement.

This is distinct from Olist static-snapshot persistence:

```text
authoritative complete snapshot
  -> FULL_REPLACE

partial keyed normal ingestion
  -> MERGE

explicit bounded replay/reprocessing
  -> replaceWhere
```

### 7. Keyless snapshot datasets remain valid

A complete authoritative snapshot does not require an artificial key merely to satisfy a persistence mechanism.

Olist Geolocation intentionally has no dataset key contract because exact duplicate source observations are legitimate source data. `FULL_REPLACE` preserves the accepted source snapshot without fabricating identity or deduplicating source rows.

### 8. Current Olist Silver keeps deterministic full-snapshot semantics

The currently delivered Silver datasets are derived from complete accepted Bronze snapshots and therefore use protected full replacement.

Silver owns analytical typing, grain, relationships, referential checks, and downstream semantics. It must validate those contracts before replacing the target.

Idempotency for Silver snapshot reruns is defined over business and lineage state. Operational fields such as `silver_processed_timestamp` may change between reruns.

This ADR does not create a generic `SilverWriter`. Shared Silver persistence/orchestration abstractions require observed repetition and a separate architectural decision.

## Alternatives considered

### Use MERGE for every dataset that has a logical key

Rejected.

A key enables matching but does not prove that an incoming batch is partial. With an authoritative complete snapshot, a basic upsert MERGE preserves target rows that no longer exist in the source snapshot. Adding delete-not-matched semantics would reproduce full-snapshot replacement with more complexity and would still not solve intentionally keyless snapshots.

### Use replaceWhere for all overwrite behavior

Rejected.

`replaceWhere` requires a meaningful bounded predicate. A complete static Olist dataset has no narrower authoritative scope than the dataset target itself. Inventing a predicate would add ceremony without changing semantics.

### Append every snapshot and model snapshot history in Bronze

Rejected for the current Olist source contract.

The repository currently models these public files as the accepted source state, not as a time-series delivery feed. Repeated ingestion is expected to be semantically idempotent rather than accumulate duplicate historical copies.

If future source deliveries provide meaningful snapshot versions that must be retained, the history model must be designed explicitly.

### Treat all sources as FULL_REPLACE for simplicity

Rejected.

API/JDBC/incremental sources may provide partial state, bounded ranges, or independent logical keys. Full replacement without complete-source authority can destroy valid target data.

## Consequences

### Positive

- persistence semantics match the actual Olist source-delivery model;
- stale target rows cannot survive a complete authoritative snapshot;
- keyless source-faithful datasets remain representable;
- rerun behavior is simple and deterministic;
- destructive writes are guarded by explicit schema/type/DQ/non-empty validation;
- normal ingestion, incremental keyed ingestion, and bounded reprocessing remain distinct concepts.

### Negative / cost

- full replacement rewrites the complete target and therefore scales with snapshot size;
- the strategy depends on the source continuing to deliver complete authoritative snapshots;
- downstream consumers must not infer change history from a table that intentionally represents current accepted snapshot state;
- Silver operational timestamps prevent byte-for-byte equality across deterministic reruns even when business state is unchanged.

### Operational implications

- runtime evidence should verify stable row/key/business-state semantics across reruns;
- unexpected row-count collapse or empty input is a failure signal, not an invitation to overwrite;
- DQ results should be persisted before the protected target is replaced when first-class DQ is configured;
- deployment smoke does not substitute for snapshot runtime acceptance.

## Implementation constraints

Future implementations governed by this ADR must preserve these rules unless the ADR is superseded:

- do not switch an authoritative Olist snapshot from `FULL_REPLACE` to `MERGE` solely because it has a key;
- do not use `FULL_REPLACE` for a source batch whose completeness is unknown;
- reject unexpected empty Olist snapshots before destructive overwrite;
- evaluate blocking DQ before replacing protected targets;
- preserve exact source duplicates when the source contract allows them;
- keep schema/type contracts explicit;
- do not silently introduce incremental/CDC/SCD/history semantics into snapshot tables;
- keep `replaceWhere` explicit and bounded;
- define deterministic rerun acceptance over business/lineage state, excluding documented processing timestamps.

## Validation

The decision is considered correctly implemented when:

1. current Olist Bronze snapshot contracts use `FULL_REPLACE`;
2. Bronze full replacement rejects an empty snapshot before persistence;
3. blocking DQ prevents protected writes where first-class DQ is configured;
4. Olist Geolocation remains keyless and duplicate-preserving;
5. current Olist Silver snapshot processors reject blocking DQ and empty output before replacement;
6. repeated accepted snapshot runs preserve expected row/key/business state;
7. API/JDBC/bounded replay paths retain their separately justified `MERGE` or `replaceWhere` semantics.

## Revisit criteria

Review this ADR if:

- Olist data begins arriving as CDC, an incremental feed, or partial exports;
- snapshot size makes complete rewrite cost operationally material;
- historical snapshot retention becomes an explicit analytical requirement;
- a downstream SLA requires incremental Silver processing;
- Databricks/Delta capabilities make another strategy materially safer or more efficient without weakening source semantics;
- current Olist snapshot completeness can no longer be established.

## Related decisions

- **ADR-003** — Bronze as the first persistent landing layer with source-faithful payload semantics and explicit reprocessing boundaries.
- **ADR-004** — executable `DatasetContract`, `DeltaTableLifecycle`, and separation of lifecycle from write semantics.
- **ADR-008** — first-class Data Quality execution and persisted quality evidence.

This ADR complements those decisions and does not supersede their API/JDBC/write-lifecycle boundaries.
