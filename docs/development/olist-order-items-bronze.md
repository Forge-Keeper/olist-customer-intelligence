# Olist Order Items Bronze

## Objective

Land `olist_order_items_dataset.csv` in Bronze while preserving the authoritative Olist CSV snapshot for later Silver order-item modeling.

## Source contract

Source path:

```text
/Volumes/dev/bronze/raw_storage/raw/olist/e_commerce/olist_order_items_dataset.csv
```

Observed source columns:

- `order_id`
- `order_item_id`
- `product_id`
- `seller_id`
- `shipping_limit_date`
- `price`
- `freight_value`

DEV profiling result:

- rows: `112,650`;
- distinct `order_id`: `98,666`;
- distinct composite key (`order_id`, `order_item_id`): `112,650`;
- composite-key null rows: `0`;
- composite-key blank rows: `0`;
- composite-key duplicate groups: `0`;
- all seven source columns: `0` nulls, `0` blanks and `0` trim-difference rows;
- full-row duplicate groups: `0`.

Numeric source-shape evidence:

- `order_item_id`: integer range `1` through `21`, no zero, negative, fractional or non-parseable rows;
- `price`: range `0.85` through `6735.00`, no negative or non-parseable rows;
- `freight_value`: range `0` through `409.68`, no negative or non-parseable rows and `383` zero-value rows.

Timestamp evidence:

- `shipping_limit_date` had `0` non-parseable rows;
- observed range: `2016-09-19 00:15:34` through `2020-04-09 22:35:08`.

Relationship profiling observed zero missing distinct foreign identifiers against the sibling Orders, Products and Sellers CSV snapshots. These relationships are evidence only and are not enforced as Bronze foreign-key semantics.

## Identity decision

The Bronze natural key is:

```text
(order_id, order_item_id)
```

`order_id` alone is not unique because one order may contain multiple items. Discovery confirmed the composite key is complete and unique across all `112,650` rows.

The snapshot uses `FULL_REPLACE`, consistent with the authoritative Olist CSV snapshot pattern.

## Bronze contract

Target:

```text
${catalog}.bronze.olist_order_items
```

All source values remain strings in Bronze:

- order and item identifiers;
- product and seller identifiers;
- shipping-limit timestamp;
- item price and freight value;
- `source_file`;
- managed `ingestion_timestamp`.

Bronze validates numeric/timestamp source shape without converting the persisted source fields to analytical types.

## Data Quality

Blocking rules:

- `ORDER-ITEMS-DQ01`: snapshot is non-empty;
- `ORDER-ITEMS-DQ02`: composite natural key is non-null and provides reusable key-completeness evidence;
- `ORDER-ITEMS-DQ03`: composite natural key is unique and provides reusable key-uniqueness evidence;
- `ORDER-ITEMS-DQ04`: required non-key source attributes are non-null;
- `ORDER-ITEMS-DQ05`: `order_item_id` is a positive integer;
- `ORDER-ITEMS-DQ06`: `shipping_limit_date` parses as a timestamp;
- `ORDER-ITEMS-DQ07`: `price` and `freight_value` parse as non-negative decimals.

Observation-only rule:

- `ORDER-ITEMS-DQ08`: count zero-freight rows without rejecting or rewriting them.

The key not-null rule is intentionally isolated from other required attributes so `DataQualityRunner` can emit reusable evidence matching the exact composite key expected by `BronzeWriter.write_checked()`.

## Bronze non-goals

Bronze does not:

- join Orders, Products or Sellers;
- enforce referential integrity across independent source snapshots;
- derive item totals or order totals;
- normalize monetary values;
- infer shipping performance;
- convert source strings to persisted decimal/timestamp/integer types;
- reject source-faithful zero freight values.

Those concerns belong to Silver or downstream analytical modeling.

## Runtime acceptance

DEV runtime acceptance is pending implementation deployment. Acceptance must prove:

- successful ingestion into `dev.bronze.olist_order_items`;
- `112,650` rows persisted;
- `112,650` distinct composite keys;
- managed metadata completeness;
- successful blocking DQ evidence;
- repeatable `FULL_REPLACE` behavior on a second execution.
