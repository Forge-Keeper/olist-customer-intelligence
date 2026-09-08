# Olist Order Payments Bronze

## Scope

`olist_order_payments` lands the authoritative Olist order-payments CSV snapshot into Bronze without business transformation.

Source:

`/Volumes/<catalog>/bronze/raw_storage/raw/olist/e_commerce/olist_order_payments_dataset.csv`

Target:

`<catalog>.bronze.olist_order_payments`

## Discovery evidence

The DEV source profile established:

- 103,886 rows;
- exactly five source columns: `order_id`, `payment_sequential`, `payment_type`, `payment_installments`, `payment_value`;
- no null, blank, or trim-difference rows in any source column;
- 99,440 distinct `order_id` values;
- 103,886 distinct `(order_id, payment_sequential)` values;
- zero duplicate composite-key groups and zero exact full-row duplicates;
- `payment_sequential` is integer-shaped from 1 through 29;
- `payment_installments` is integer-shaped from 0 through 24, including two zero-installment rows;
- `payment_value` is parseable and non-negative, including nine zero-value rows;
- observed payment types: `credit_card`, `boleto`, `voucher`, `debit_card`, and `not_defined`;
- three source rows use `payment_type = 'not_defined'`;
- all distinct `order_id` values are covered by the sibling Orders source snapshot.

Cross-dataset coverage is observational evidence only and is not enforced as a Bronze foreign-key rule.

## Bronze identity and write semantics

Natural key:

`(order_id, payment_sequential)`

Write strategy:

`FULL_REPLACE`

The source is treated as a complete snapshot. Reruns replace the Bronze snapshot rather than merge payment rows incrementally.

## Persisted contract

Bronze preserves the five source fields as strings:

- `order_id`
- `payment_sequential`
- `payment_type`
- `payment_installments`
- `payment_value`

The ingestion layer also records `source_file` and the managed Bronze ingestion timestamp.

Source-field numeric normalization and business typing are intentionally deferred downstream.

## Data Quality contract

Blocking rules:

- `ORDER-PAYMENTS-DQ01` — snapshot must not be empty;
- `ORDER-PAYMENTS-DQ02` — composite natural key cannot contain nulls;
- `ORDER-PAYMENTS-DQ03` — composite natural key must be unique;
- `ORDER-PAYMENTS-DQ04` — required non-key source attributes cannot contain nulls;
- `ORDER-PAYMENTS-DQ05` — `payment_sequential` must be a positive integer-shaped value;
- `ORDER-PAYMENTS-DQ06` — `payment_installments` must be a non-negative integer-shaped value;
- `ORDER-PAYMENTS-DQ07` — `payment_value` must be a parseable non-negative decimal.

Informational observations:

- `ORDER-PAYMENTS-DQ08` counts zero-value payments;
- `ORDER-PAYMENTS-DQ09` counts zero-installment payments;
- `ORDER-PAYMENTS-DQ10` counts `payment_type = 'not_defined'` rows.

Zero-value payments, zero installments, and `not_defined` payment types are source evidence and remain source-faithful in Bronze.

## Explicit non-goals

This Bronze slice does not:

- enforce relationships to Orders;
- normalize payment-type labels;
- infer payment status or business validity;
- aggregate payments to order totals;
- reconcile payment totals with Order Items;
- convert persisted numeric strings into typed monetary/integer columns;
- reject zero-value or zero-installment source rows solely because of business semantics.

Those concerns belong to downstream modeling unless a separate Bronze requirement is approved.

## DEV runtime acceptance

DEV runtime acceptance is complete.

Execution evidence:

- first Databricks run `944861675496142` completed with `TERMINATED SUCCESS`, application run ID `029b4e3c-ddb3-4901-8eb1-1d20c9050f48`, and 103,886 ingested rows;
- second Databricks run `583140817447126` completed with `TERMINATED SUCCESS`, application run ID `21e379b6-0a7f-458c-a5d7-78e15ed49cc6`, and 103,886 ingested rows;
- both executions used `FULL_REPLACE` against `dev.bronze.olist_order_payments`;
- post-rerun integrity evidence showed 103,886 rows, 103,886 distinct `(order_id, payment_sequential)` keys, zero null `source_file` values, and zero null ingestion timestamps.

The stable semantic cardinality across both successful runs demonstrates snapshot rerun idempotence for the approved source snapshot.
