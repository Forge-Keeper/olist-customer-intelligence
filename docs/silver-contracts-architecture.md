# Silver Contracts & Architecture — Customers + Orders

Status: proposed architecture for human review  
Tracking: GitHub Issue #104  
Depends on: #101 Silver Discovery & Conformed Model  
Implementation issue: #105

## 1. Purpose

Define the minimum contracts required to implement the first Olist Silver vertical slice without introducing a generic Silver framework before repetition exists.

The accepted discovery established the customer identity model and DEV data behavior. This document freezes only the semantics needed by `customers + orders`.

## 2. Architectural boundary

Bronze remains source-faithful and string-oriented. Silver owns:

- analytical typing;
- explicit grain and relationship semantics;
- deterministic harmonization;
- blocking Data Quality before protected writes;
- non-blocking anomaly evidence where source behavior disproves a universal invariant;
- lineage sufficient to trace a Silver row to its Bronze input state.

Silver does not own Gold aggregations, Customer 360, incremental checkpoints, SCD history, generic surrogate keys, or geography canonicalization in this slice.

## 3. Accepted runtime evidence

### Customers DEV

- rows: 99,441;
- distinct `customer_id`: 99,441;
- null `customer_id`: 0;
- distinct `customer_unique_id`: 96,096;
- null `customer_unique_id`: 0;
- 2,997 `customer_unique_id` values map to multiple `customer_id` values;
- maximum observed multiplicity: 17;
- 252 longitudinal identities have multiple observed customer locations.

### Orders DEV

- rows: 99,441;
- distinct `order_id`: 99,441;
- distinct `customer_id`: 99,441;
- null `order_id`: 0;
- null `customer_id`: 0;
- Orders -> Customers orphan count: 0;
- all five lifecycle timestamp fields parse successfully;
- null counts: `approved_at=160`, `carrier_date=1,783`, `customer_delivery=2,965`;
- purchase and estimated delivery have zero nulls;
- temporal observations: approval-before-purchase=0, carrier-before-approval=1,359, delivered-before-carrier=23, delivered-before-purchase=0.

These are DEV observations for the accepted snapshot, not universal source guarantees.

## 4. Silver Customers contract

### Grain

One row per `customer_id`.

`customer_id` remains the transactional/source customer identifier referenced by Orders.

`customer_unique_id` is the longitudinal identity used by downstream customer analytics. It must not replace `customer_id` as the Orders relationship key.

### Proposed persisted schema

| Column | Type | Nullable | Semantics |
| --- | --- | :---: | --- |
| `customer_id` | STRING | no | Silver grain / source transactional customer identifier |
| `customer_unique_id` | STRING | no | longitudinal customer identity |
| `customer_zip_code_prefix` | STRING | yes | transaction-time customer ZIP prefix; leading zeroes preserved |
| `customer_city` | STRING | yes | source customer city, trimmed only if the implementation proves source whitespace is non-semantic |
| `customer_state` | STRING | yes | source customer state code |
| `source_file` | STRING | yes | Bronze source-file lineage |
| `bronze_ingestion_timestamp` | TIMESTAMP | yes | Bronze `ingestion_timestamp` renamed at the Silver boundary for provenance clarity |
| `silver_processed_timestamp` | TIMESTAMP | no | timestamp of the Silver transformation run |

### Customer identity rule

A single `customer_unique_id` may legitimately have multiple `customer_id` values and multiple observed locations. Silver therefore does not collapse Customers to one row per `customer_unique_id` and does not select a canonical customer address.

A future Customer 360 may derive current/last-known address using an explicit downstream rule.

## 5. Silver Orders contract

### Grain

One row per `order_id`.

### Proposed persisted schema

| Column | Type | Nullable | Semantics |
| --- | --- | :---: | --- |
| `order_id` | STRING | no | Silver grain / source order identifier |
| `customer_id` | STRING | no | semantic FK to Silver Customers |
| `order_status` | STRING | no | source order lifecycle status |
| `order_purchase_timestamp` | TIMESTAMP | no | purchase time |
| `order_approved_at` | TIMESTAMP | yes | approval time |
| `order_delivered_carrier_date` | TIMESTAMP | yes | carrier handoff time |
| `order_delivered_customer_date` | TIMESTAMP | yes | customer delivery time |
| `order_estimated_delivery_date` | TIMESTAMP | no | source estimated delivery time |
| `source_file` | STRING | yes | Bronze source-file lineage |
| `bronze_ingestion_timestamp` | TIMESTAMP | yes | Bronze `ingestion_timestamp` renamed at the Silver boundary for provenance clarity |
| `silver_processed_timestamp` | TIMESTAMP | no | timestamp of the Silver transformation run |

No additional order-derived measures belong in this first contract. Durations such as approval latency or delivery delay should be added only when a real reusable consumer requirement appears.

## 6. Type conversion semantics

Silver transformations must use explicit casts rather than schema inference.

For the accepted source fields:

- identifiers/status/geography remain STRING;
- lifecycle date/time fields become TIMESTAMP;
- ZIP prefixes remain STRING to preserve leading zeroes.

A non-null Bronze value that fails conversion to the required Silver type is a blocking Data Quality failure. The protected target must not be overwritten with partially converted data.

Nullable timestamp fields may remain null when the Bronze value is null.

## 7. Relationship contract

`silver.olist_orders.customer_id` semantically references `silver.olist_customers.customer_id`.

The first accepted DEV snapshot contains zero orphans. The Silver contract therefore treats orphan Orders as a blocking referential-integrity failure.

The relationship is modeled as Customers 1 -> N Orders even though the accepted DEV snapshot currently has one distinct `customer_id` per order. The implementation must not encode the current accidental one-order-per-`customer_id` observation as a uniqueness constraint on Orders.customer_id.

## 8. Data Quality policy

### Blocking — Customers

- `customer_id` non-null;
- `customer_id` unique;
- `customer_unique_id` non-null;
- required output schema/type compatibility;
- required type conversions successful.

No rule requires `customer_unique_id` uniqueness.

### Blocking — Orders

- `order_id` non-null;
- `order_id` unique;
- `customer_id` non-null;
- `order_status` non-null;
- `order_purchase_timestamp` non-null and parseable;
- `order_estimated_delivery_date` non-null and parseable;
- optional lifecycle timestamps parseable when present;
- zero Orders -> Customers orphans;
- when approval exists: `order_approved_at >= order_purchase_timestamp`;
- when delivery exists: `order_delivered_customer_date >= order_purchase_timestamp`.

### Non-blocking / anomaly evidence

The following are explicitly not universal blocking invariants because DEV disproves them:

- `order_delivered_carrier_date >= order_approved_at` — 1,359 counterexamples observed;
- `order_delivered_customer_date >= order_delivered_carrier_date` — 23 counterexamples observed.

They may be recorded as WARNING/observability metrics with stable rule IDs.

### Not yet asserted

No blocking rule is currently defined for:

- estimated delivery relative to purchase or actual delivery;
- status-dependent nullability;
- allowed status enumeration;
- canonical geography.

Those require a separate evidence basis before becoming contracts.

## 9. Persistence and idempotency

The first Silver slice uses deterministic full-snapshot replacement because the Olist Bronze inputs are static snapshot datasets and their current write contracts are `FULL_REPLACE`.

Required behavior:

1. read the accepted Bronze snapshot;
2. transform in memory/logical plan;
3. evaluate blocking DQ before protected replacement;
4. if blocking DQ fails, preserve the previous Silver target unchanged;
5. if DQ passes, replace the complete target atomically using the existing Delta lifecycle primitives where they fit;
6. rerunning against the same Bronze business state produces the same Silver business rows and keys.

`silver_processed_timestamp` is operational metadata and may change across reruns; idempotency is defined over the business/lineage state, not byte-for-byte equality of the processing timestamp.

No MERGE, checkpoint, CDC, SCD, or bounded replay semantics are introduced yet.

## 10. Lineage contract

The first slice preserves only lineage that is concretely useful:

- `source_file`: source CSV lineage inherited from Bronze;
- `bronze_ingestion_timestamp`: Bronze ingestion timestamp, renamed to prevent confusion with the Silver processing time;
- `silver_processed_timestamp`: time the Silver output was produced;
- existing Control Plane `run_id` / DQ evidence remains operational evidence rather than a duplicated business-table column unless implementation constraints prove row-level run correlation is required.

This intentionally avoids copying every Bronze technical field into Silver.

## 11. Schema drift behavior

Silver persisted schemas are explicit.

- missing required Bronze columns: fail before write;
- incompatible source type/content: fail before write;
- unexpected extra Bronze columns: do not automatically propagate to Silver;
- Silver schema evolution requires an explicit contract change;
- no silent widening or automatic field passthrough.

This keeps Silver consumer contracts stable even if Bronze evolves source-faithfully.

## 12. Reuse of existing platform capabilities

The implementation should first reuse existing capabilities where their contracts fit:

- `DatasetContract` for persisted schema/key/metadata if it is layer-neutral enough in practice;
- `DeltaTableLifecycle` for managed Delta table lifecycle;
- existing Data Quality contracts/runner/evidence persistence;
- Control Plane execution tracking.

The implementation must not create `SilverWriter` preemptively.

If Customers and Orders independently expose repeated orchestration/write code with equivalent semantics, the repetition should be documented during #105. Extraction into a shared capability is then a separate architecture decision.

## 13. Dataset naming and package boundary

Proposed tables:

- `dev.silver.olist_customers`
- `dev.silver.olist_orders`

Equivalent environment-resolved names apply to STG/PRD through DAB configuration; domain logic must not hard-code environment catalogs.

Proposed code ownership:

```text
src/olist_data_platform/domains/silver/olist/
  customers_*.py
  orders_*.py

src/olist_data_platform/jobs/
  ...Silver job composition as required...
```

Exact file decomposition should remain implementation-local until repetition justifies a stronger pattern.

## 14. Testing strategy

### Unit

- deterministic column selection/typing;
- customer identity preservation;
- timestamp conversion;
- nullable timestamp behavior;
- blocking temporal rules;
- non-blocking anomaly rules;
- no accidental collapse by `customer_unique_id`.

### Integration

- complete Silver schema persisted as declared;
- full replacement removes stale target rows;
- failed blocking DQ preserves previous target state;
- Orders -> Customers orphan gate;
- rerun against identical business input preserves row/key/business-state equality.

### DEV runtime acceptance

Customers:

- 99,441 rows expected for the current accepted Bronze snapshot;
- 99,441 distinct `customer_id`;
- 96,096 distinct `customer_unique_id`;
- zero blocking DQ failures.

Orders:

- 99,441 rows expected for the current accepted Bronze snapshot;
- 99,441 distinct `order_id`;
- zero Orders -> Customers orphans;
- zero conversion failures;
- non-blocking anomaly counts reconciled with discovery unless the Bronze snapshot changes.

Acceptance evidence must record the exact source/run context so these counts are not generalized to future snapshots.

## 15. Deployment/runtime separation

Deployment smoke and runtime acceptance remain separate:

- deployment smoke proves the declared DAB/job wiring can start and complete its representative path;
- runtime acceptance proves Silver schemas, counts, DQ, relationships, idempotency and protected-write behavior.

A successful smoke does not mark the Silver datasets DONE.

## 16. Implementation sequence for #105

1. implement Customers transformation + contract + DQ;
2. validate locally/integration;
3. implement Orders transformation + contract + DQ;
4. add Orders -> Customers referential check;
5. wire the minimum executable job/DAB resources;
6. run DEV Customers;
7. run DEV Orders;
8. rerun to verify deterministic full-snapshot behavior;
9. deliberately exercise at least one controlled blocking-DQ failure and verify target preservation;
10. record runtime evidence and update Platform Status only at closeout.

## 17. Explicit non-decisions

This architecture does not decide:

- `SilverWriter`;
- SCD type/history;
- surrogate keys;
- incremental checkpoints;
- Customer 360 grain;
- conformed geography grain;
- order status taxonomy;
- derived order metrics;
- later Silver datasets.

## 18. Human architecture gate

Approval of this document freezes the following for #105:

1. Customers grain = `customer_id`;
2. Orders grain = `order_id`;
3. Orders FK semantics use `customer_id`;
4. `customer_unique_id` remains longitudinal identity;
5. customer location remains at `customer_id` grain;
6. lifecycle strings become TIMESTAMP with the documented nullability;
7. full-snapshot protected replacement is the initial persistence strategy;
8. blocking/non-blocking DQ classification follows Section 8;
9. Silver carries `source_file`, renamed `bronze_ingestion_timestamp`, and `silver_processed_timestamp` as the initial lineage columns;
10. no shared Silver abstraction is introduced before implementation demonstrates repetition.

Any deviation from these items during #105 is a new architecture gate rather than an implementation convenience.
