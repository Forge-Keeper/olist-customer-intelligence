# Olist Silver Customers + Orders — DEV Closeout

## Scope

This record closes the first delivered Olist Silver vertical slice in DEV: `olist_customers` and `olist_orders`.

Implementation was delivered by PR #109 and follows the contracts accepted in #104 and the runtime discovery captured in #101.

## Runtime acceptance

Accepted DEV runtime evidence:

### Silver Customers

- row count: `99,441`;
- distinct `customer_id`: `99,441`;
- distinct `customer_unique_id`: `96,096`;
- null `customer_id`: `0`;
- null `customer_unique_id`: `0`.

The accepted grain remains one row per `customer_id`. `customer_unique_id` is retained as longitudinal identity and is not substituted for the transactional grain.

### Silver Orders

- row count: `99,441`;
- distinct `order_id`: `99,441`;
- distinct `customer_id`: `99,441`;
- null `order_id`: `0`;
- null `customer_id`: `0`;
- Orders -> Customers orphan count: `0`.

Lifecycle fields are persisted as `TIMESTAMP`:

- `order_purchase_timestamp`;
- `order_approved_at`;
- `order_delivered_carrier_date`;
- `order_delivered_customer_date`;
- `order_estimated_delivery_date`.

Persisted lineage is:

- `source_file`;
- `bronze_ingestion_timestamp`;
- `silver_processed_timestamp`.

## Data Quality evidence

The accepted normal DEV run produced:

- all blocking Orders rules `DQ01` through `DQ07` = `PASS`;
- `DQ08` = `WARNING / FAIL`, `invalid_row_count=1359` for carrier handoff preceding approval;
- `DQ09` = `WARNING / FAIL`, `invalid_row_count=23` for customer delivery preceding carrier handoff.

Those two temporal patterns remain observability signals rather than global write blockers because runtime discovery proved they are present in the accepted source snapshot.

## Idempotence acceptance

The same deployed artifact was rerun against the same Bronze state without a redeploy.

Business state plus Bronze lineage was compared before and after with bidirectional `EXCEPT ALL`, deliberately excluding `silver_processed_timestamp` because that field represents processing time and is expected to change between runs.

Results:

- Customers `rows_only_before = 0`;
- Customers `rows_only_after = 0`;
- Orders `rows_only_before = 0`;
- Orders `rows_only_after = 0`.

This proves deterministic rerun behavior for the accepted business state.

## Protected-write rejection acceptance

A controlled DEV validation removed exactly one customer from a temporary Silver Customers copy and executed only the `silver_orders` task against:

- canonical `dev.bronze.olist_orders` as source;
- temporary incomplete Customers table;
- temporary protected Orders target;
- canonical DEV administrative DQ history.

The run was rejected with:

- `DataQualityRejectedError`;
- blocking rule `OLIST-SILVER-ORDERS-DQ05`;
- persisted DQ evidence `severity=ERROR`, `status=FAIL`, `invalid_row_count=1`.

The implementation persists DQ evidence before calling `raise_for_blocking_failures()`, so the rejection is auditable even though the write does not occur.

Target preservation was then proven with bidirectional `EXCEPT ALL` against the valid pre-test snapshot:

- `rows_only_before = 0`;
- `rows_only_after = 0`.

Therefore a blocking referential-integrity failure prevents the `FULL_REPLACE` and preserves the previously valid target.

## Accepted semantics

The delivered slice therefore proves in DEV:

1. explicit Silver grains and typed persisted schemas;
2. preserved transactional and longitudinal customer identity semantics;
3. Orders -> Customers referential integrity;
4. blocking vs non-blocking DQ policy;
5. persisted DQ evidence;
6. deterministic `FULL_REPLACE` reruns;
7. protected target behavior on blocking DQ;
8. explicit source-to-Silver lineage;
9. no generic `SilverWriter`, SCD, incremental checkpointing, surrogate-key framework, or geography canonicalization.

## Environment boundary

This closeout is DEV runtime acceptance only. It does not imply full STG or PRD runtime acceptance for these Silver datasets. Deployment-smoke evidence, when present, remains distinct from runtime acceptance.

## DONE

For the accepted DEV scope, the first Olist Silver Customers + Orders vertical slice is DONE once this closeout and the corresponding Platform Status update are merged.