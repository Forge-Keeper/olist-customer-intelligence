# Silver Products + Category + Sellers + Order Items — Implementation

Issue: #115
Architecture gate: #114

This delivery implements the second Olist Silver slice after Customers + Orders.

## Scope

- Product Category Translation Silver lookup;
- Products Silver with typed attributes and nullable English translation;
- Sellers Silver;
- Order Items Silver with typed sequence/timestamp/monetary fields and referential DQ;
- deterministic `FULL_REPLACE` protected by persisted Data Quality evidence;
- explicit Bronze lineage carried into Silver;
- DAB task dependency graph;
- unit and integration coverage;
- DEV runtime acceptance before Platform Status closeout.

## Architecture constraints

The implementation preserves the decisions frozen in #114:

- no generic `SilverWriter`;
- no surrogate keys;
- no incremental/CDC processing;
- no geography canonicalization;
- no Gold modeling;
- untranslated product categories are non-blocking observations;
- blocking DQ must reject the snapshot before target replacement.

## DEV runtime acceptance

Accepted on the `dev` environment with the wheel built from merge commit `da787c47b8357a0a0d0265efebbd7b77b8c29a74` after the operational metadata-concurrency fix from #117.

### Successful slice execution

The DAB job `olist_silver_products_category_sellers_order_items` completed `SUCCESS` with:

- Product Category Translation: 71 rows;
- Sellers: 3,095 rows;
- Products: 32,951 rows;
- Order Items: 112,650 rows.

The accepted dataset checks confirmed:

- Category Translation: 71 rows, 71 distinct `product_category_name`, zero null source categories, zero null English categories;
- Products: 32,951 rows, 32,951 distinct `product_id`, zero null IDs, 13 untranslated non-null categories, 4 zero-weight products;
- Sellers: 3,095 rows, 3,095 distinct `seller_id`, zero null IDs;
- Order Items: 112,650 rows, 112,650 distinct `(order_id, order_item_id)` keys, zero null required IDs/FKs;
- Order Items -> Orders orphans: 0;
- Order Items -> Products orphans: 0;
- Order Items -> Sellers orphans: 0.

Persisted Silver types were also confirmed in DEV:

- Products renamed the source typo fields at the Silver boundary and persisted integer/decimal physical attributes according to #114;
- Order Items persisted `order_item_id` as `INT`, `shipping_limit_date` as `TIMESTAMP`, and `price` / `freight_value` as `DECIMAL(18,2)`;
- Bronze lineage remains available through `source_file` and `bronze_ingestion_timestamp`, with `silver_processed_timestamp` added at Silver.

### Deterministic rerun

A later rerun of the same DAB job completed `SUCCESS` with the same semantic row counts for all four datasets.

Before the rerun, validation snapshots excluded only `silver_processed_timestamp`. Bidirectional `EXCEPT ALL` comparisons after the rerun returned `0/0` for:

- Product Category Translation;
- Products;
- Sellers;
- Order Items.

This proves semantic idempotency of the accepted static-snapshot `FULL_REPLACE` implementation while allowing the expected processing timestamp to change between runs.

### Controlled blocking-DQ preservation test

A validation-only Products parent table intentionally removed one product referenced by Bronze Order Items. That produced 9 controlled Order Items -> Products orphan rows.

Running only the Silver Order Items entry point against the validation parents and a protected validation target failed as expected with:

- `DataQualityRejectedError`;
- blocking rule `OLIST-SILVER-ORDER-ITEMS-DQ05`;
- severity `ERROR`;
- status `FAIL`;
- `invalid_row_count=9`;
- all other Order Items blocking rules in that validation run remained `PASS`.

The protected target was compared bidirectionally before and after the rejected run, excluding only `silver_processed_timestamp`; both comparisons returned `0` rows.

Accepted behavior is therefore:

```text
transform
  -> evaluate Data Quality
  -> persist DQ evidence
  -> blocking failure
  -> abort before FULL_REPLACE
  -> preserve previous target
```

## Runtime incident and correction

The first DEV execution exposed a separate platform-level concurrency defect: parallel Silver tasks were repeatedly reconciling metadata on shared operational tables (`execution_runs` and `data_quality_results`) from the runtime hot path, which triggered Delta metadata conflicts.

Issue #117 corrected this by allowing existing tables to be schema/layout validated without re-running metadata reconciliation from the shared operational writers. Default lifecycle behavior remains unchanged for provisioning and ordinary lifecycle use. The corrected implementation passed CI and the subsequent parallel DEV rerun completed successfully.

## Closeout

The second Olist Silver slice is accepted in DEV for:

- Product Category Translation;
- Products;
- Sellers;
- Order Items.

Accepted evidence covers explicit typed contracts, lineage, referential DQ, expected non-blocking warnings, deterministic reruns, and protected target behavior on blocking rejection. STG and PRD runtime acceptance for these Silver datasets remains unproven and must not be inferred from DEV or deployment-smoke evidence.
