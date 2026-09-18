# Silver Order Payments — Implementation

Issue: #133  
Gate-1 baseline: `main@a1b1c0127bf1fb11fb71288f482474a769e26f49`  
Implementation baseline: `dev@b35f20e61fdff0eadab4da4eadfb841eb989c8ae`  
Branch: `feature/133-silver-order-payments`

## Status

Implementation is prepared for CI and external implementation review.

DEV runtime acceptance is still pending and **no Silver Order Payments readiness claim is made by this document**.

## Delivered scope

The implementation adds:

- typed `silver.olist_order_payments` domain contract;
- grain `(order_id, payment_sequential)`;
- explicit `INT` typing for payment sequence and installments;
- exact `DECIMAL(18,2)` typing for payment value;
- blocking Payments -> Silver Orders referential DQ;
- informational observations for zero value, zero installments and `not_defined`;
- Bronze lineage and `silver_processed_timestamp`;
- protected `FULL_REPLACE` through the approved `SilverSnapshotWriter`;
- packaged `olist-silver-order-payments` job;
- DAB ordering after `silver_orders`;
- deployment-smoke dependency on Bronze Order Payments;
- targeted unit/integration coverage.

## Gate-1 review reconciliation

The external Design review returned `APPROVED` / `READY FOR IMPLEMENTATION`.

### Monetary exactness

The reviewer identified that the existing Order Items pattern is not sufficient proof of scale-exactness because Spark may round excess fractional scale when casting to `DECIMAL(18,2)`.

Order Payments therefore does **not** copy that evidence shape.

The source `payment_value` text must:

- use plain decimal notation;
- contain at most 16 integer digits;
- avoid exponent notation;
- cast successfully to `DECIMAL(18,2)`;
- contain no non-zero fractional digit after the second decimal place.

Examples:

- `99.3300` — accepted as exactly `99.33`;
- `99.335` — rejected;
- `0.0000000000000000001` — rejected;
- `1e2` — rejected;
- 17 or more integer digits — rejected.

The exactness evidence remains temporary and is never persisted in the Silver target.

### Integer overflow

Silver uses `INT` because the accepted DEV source ranges are small.

A Bronze-valid BIGINT outside the INT range is still rejected in Silver through DQ03. Regression coverage includes `2147483648`.

### DAB coupling trade-off

`silver_order_payments` is appended to the existing `olist_silver_customers_orders` job after `silver_orders`.

Accepted benefit:

- direct Orders dependency is explicit inside the DAB task graph;
- no additional DAB/smoke job contract is introduced.

Accepted cost:

- a Payments failure marks the combined job failed even after Customers/Orders completed;
- Bronze Payments smoke failure can block this job and transitively the second Silver smoke job.

Targets remain independently protected and execution tracking remains per dataset.

Revisit this placement if job-level status becomes a consumer boundary or if isolated smoke signals become an operational requirement.

## Protected write

Order Payments reuses `SilverSnapshotWriter` without expanding its contract:

```text
transformed payment rows
  -> Data Quality evaluation
  -> persist DQ evidence
  -> blocking gate
  -> empty-snapshot guard
  -> Delta lifecycle
  -> project DatasetContract columns
  -> FULL_REPLACE
```

Temporary columns such as `_invalid_typed_cast` and `_order_exists` are excluded from persisted contract columns.

## Tests

Targeted coverage includes:

- persisted schema and composite business key;
- multiple legitimate payments for the same order;
- lineage preservation;
- zero-value / zero-installment / `not_defined` observations;
- monetary exactness cases;
- INT overflow;
- negative numeric domain rejection;
- duplicate composite key rejection;
- Orders FK rejection;
- protected-target behavior on blocking DQ;
- job execution tracking and explicit input reads;
- DAB/smoke dependency regression.

## DEV runtime acceptance still required

Before `docs/platform-status.md` can mark the dataset DEV-ready, retain:

- successful DAB run IDs and application run ID;
- target row count;
- distinct composite-key count;
- distinct `order_id` count;
- Payments -> Orders orphan count;
- physical persisted types;
- zero-value / zero-installment / `not_defined` counts;
- maximum observed fractional-digit count for source `payment_value`;
- minimum and maximum source `payment_value`;
- lineage completeness;
- deterministic semantic rerun using bidirectional `EXCEPT ALL` excluding only `silver_processed_timestamp`;
- controlled FK rejection with persisted DQ evidence and unchanged target.

Deployment smoke remains a separate evidence class and does not replace DEV runtime acceptance.
