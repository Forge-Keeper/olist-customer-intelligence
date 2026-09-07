# Olist Orders Bronze

## Objective

Land `olist_orders_dataset.csv` in Bronze while preserving the source snapshot for later Silver order-lifecycle modeling.

## Source contract

Source path:

```text
/Volumes/dev/bronze/raw_storage/raw/olist/e_commerce/olist_orders_dataset.csv
```

Observed source columns:

- `order_id`
- `customer_id`
- `order_status`
- `order_purchase_timestamp`
- `order_approved_at`
- `order_delivered_carrier_date`
- `order_delivered_customer_date`
- `order_estimated_delivery_date`

DEV profiling result:

- rows: `99,441`;
- distinct `order_id`: `99,441`;
- null `order_id`: `0`;
- null `customer_id`: `0`;
- null `order_status`: `0`;
- null `order_purchase_timestamp`: `0`;
- null `order_approved_at`: `160`;
- null `order_delivered_carrier_date`: `1,783`;
- null `order_delivered_customer_date`: `2,965`;
- null `order_estimated_delivery_date`: `0`.

Observed statuses:

- `approved`;
- `canceled`;
- `created`;
- `delivered`;
- `invoiced`;
- `processing`;
- `shipped`;
- `unavailable`.

All five timestamp source columns had zero non-null values that failed `TRY_CAST(... AS TIMESTAMP)` in the DEV profile.

No status-domain semantics or lifecycle ordering constraints are introduced in Bronze.

## Identity decision

`order_id` is the Bronze natural key and is enforced as non-null and unique by Data Quality. The DEV profile confirmed `99,441` rows and `99,441` distinct order IDs.

The snapshot uses `FULL_REPLACE`, consistent with the current Olist CSV snapshot pattern.

## Bronze contract

Target:

```text
${catalog}.bronze.olist_orders
```

Source values are persisted as strings:

- order/customer identifiers;
- order status;
- purchase, approval, carrier-delivery, customer-delivery and estimated-delivery timestamps;
- `source_file`;
- managed `ingestion_timestamp`.

Approval and actual delivery timestamps remain nullable because DEV profiling confirms missing lifecycle events in the source. Purchase and estimated-delivery timestamps are required and had zero nulls in the DEV profile.

## Data Quality

Blocking rules:

- `ORDERS-DQ01`: snapshot is non-empty;
- `ORDERS-DQ02`: order ID, customer ID, status, purchase timestamp and estimated-delivery timestamp are non-null;
- `ORDERS-DQ03`: `order_id` is unique;
- `ORDERS-DQ04`: present timestamp values parse as timestamps.

Observation-only rules:

- `ORDERS-DQ05`: count orders without approval timestamp;
- `ORDERS-DQ06`: count orders without customer delivery timestamp.

The observed DEV profile is compatible with the initial DQ contract: no blocking condition is expected from source shape, while DQ05 and DQ06 capture genuine source incompleteness without altering it.

## Bronze non-goals

Bronze does not:

- normalize or remap order statuses;
- infer a canonical lifecycle state;
- enforce timestamp ordering between lifecycle events;
- calculate delivery delay or lead time;
- join customers, items, payments or reviews;
- repair missing timestamps;
- convert timestamp source fields to persisted timestamp types.

Those concerns belong to Silver or downstream modeling.

## DEV runtime acceptance pending

Source profiling is complete. Runtime acceptance still must confirm:

1. successful first `FULL_REPLACE` run with `99,441` source/persisted rows;
2. target integrity: `99,441` rows, `99,441` distinct order IDs and non-null managed metadata;
3. unchanged semantic state after a second `FULL_REPLACE` run.
