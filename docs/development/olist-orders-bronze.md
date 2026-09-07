# Olist Orders Bronze

## Objective

Land `olist_orders_dataset.csv` in Bronze while preserving the source snapshot for later Silver order-lifecycle modeling.

## Source contract

Expected source path:

```text
/Volumes/${catalog}/bronze/raw_storage/raw/olist/e_commerce/olist_orders_dataset.csv
```

Expected source columns:

- `order_id`
- `customer_id`
- `order_status`
- `order_purchase_timestamp`
- `order_approved_at`
- `order_delivered_carrier_date`
- `order_delivered_customer_date`
- `order_estimated_delivery_date`

Runtime profiling in DEV is still required before acceptance is closed. This implementation deliberately avoids introducing status-domain semantics or lifecycle ordering rules before those source facts are verified.

## Identity decision

`order_id` is the Bronze natural key candidate and is enforced as non-null and unique by Data Quality.

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

The approval and actual delivery timestamps are nullable because lifecycle events may not exist for every source order. Purchase and estimated-delivery timestamps are required by the initial contract and must be verified in DEV profiling.

## Data Quality

Blocking rules:

- `ORDERS-DQ01`: snapshot is non-empty;
- `ORDERS-DQ02`: order ID, customer ID, status, purchase timestamp and estimated-delivery timestamp are non-null;
- `ORDERS-DQ03`: `order_id` is unique;
- `ORDERS-DQ04`: present timestamp values parse as timestamps.

Observation-only rules:

- `ORDERS-DQ05`: count orders without approval timestamp;
- `ORDERS-DQ06`: count orders without customer delivery timestamp.

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

## DEV acceptance pending

Before promotion, DEV runtime acceptance must confirm:

1. source file and exact schema;
2. row count and distinct `order_id` count;
3. null counts for all source columns;
4. observed `order_status` values;
5. timestamp parsing compatibility;
6. successful first `FULL_REPLACE` run;
7. unchanged semantic state after a second run.
