# Silver Discovery & Conformed Model

Status: DEV profiling complete for the first Customers + Orders vertical slice  
Tracking: GitHub Issue #101  
Scope: Olist analytical Silver only; no transformation implementation in this change.

## 1. Evidence boundary

This document separates three evidence levels:

- **Repository fact**: directly declared by `main` contracts, code, or canonical Platform Status.
- **Accepted runtime fact**: execution evidence observed in DEV and recorded in the issue/discovery.
- **Proposed model**: analytical interpretation derived from repository/runtime evidence and subject to architecture review before implementation.

Bronze remains source-faithful. Silver is responsible for typing, harmonization, conformance, explicit relationship semantics, and quality rules justified by the analytical model.

## 2. Current Olist Bronze inventory

`main` contains code for the complete 11-source public Olist CSV boundary.

| Bronze dataset | Repository-declared grain | Declared key | Important relationship fields | Initial Silver role |
| --- | --- | --- | --- | --- |
| Customers | one source customer row | `customer_id` | `customer_unique_id`, geography fields | customer identity / order-customer bridge |
| Sellers | one source seller row | `seller_id` | geography fields | seller entity |
| Marketing Qualified Leads | one source lead row | `mql_id` | landing page, origin | seller acquisition funnel |
| Closed Deals | one source closed-deal row | `mql_id` | nullable `seller_id` | lead-to-seller commercial bridge |
| Products | one source product row | `product_id` | `product_category_name` | product entity |
| Product Category Translation | one translation row | `product_category_name` | English category name | product category conforming lookup |
| Geolocation | one raw geolocation observation | none | ZIP prefix, city, state, lat/lng | candidate geographic conformance input |
| Orders | one source order row | `order_id` | `customer_id`, lifecycle timestamps | order lifecycle fact/entity |
| Order Items | one item sequence within order | (`order_id`, `order_item_id`) | `product_id`, `seller_id` | order line fact |
| Order Payments | one payment sequence within order | (`order_id`, `payment_sequential`) | payment attributes | payment fact |
| Order Reviews | one review/order association | (`review_id`, `order_id`) | score, creation/answer timestamps | review fact |

All Olist Bronze contracts currently use `FULL_REPLACE`; most scalar source attributes are intentionally persisted as strings and should be typed only in Silver.

## 3. Customer identity — accepted DEV evidence

Accepted DEV profile:

- Customers row count: `99,441`;
- distinct `customer_id`: `99,441`;
- null `customer_id`: `0`;
- distinct `customer_unique_id`: `96,096`;
- null `customer_unique_id`: `0`;
- `93,099` longitudinal identities map to exactly one `customer_id`;
- `2,997` longitudinal identities map to multiple `customer_id` values;
- maximum observed multiplicity: `17 customer_id` values for one `customer_unique_id`;
- `252 customer_unique_id` values have more than one distinct observed customer location.

These results validate two separate concepts:

- **`customer_id`** is the source transactional identity and remains the Silver Customers key/grain used by Orders.
- **`customer_unique_id`** is a longitudinal identity used to group multiple transactional customer records belonging to the same underlying customer.

Therefore:

```text
customer_unique_id
    longitudinal identity
           |
           | 1:N observed
           v
customer_id
    Silver Customers grain
           |
           | 1:1 observed in current Orders snapshot
           v
order_id
    Silver Orders grain
```

The current snapshot has one distinct `customer_id` per order and one order per observed `customer_id`, but the Silver contract should still preserve the semantic distinction rather than assume that `customer_unique_id` is the order foreign key.

The `252` longitudinal identities with multiple locations also prove that customer location cannot be safely collapsed to a single canonical attribute at `customer_unique_id` grain without an explicit temporal/current-address rule. Initial Silver should retain geography on the `customer_id` row.

## 4. Orders — accepted DEV evidence

Accepted DEV profile:

- Orders row count: `99,441`;
- distinct `order_id`: `99,441`;
- distinct `customer_id`: `99,441`;
- null `order_id`: `0`;
- null `customer_id`: `0`;
- Orders -> Customers orphan count: `0`.

### Status distribution

| order_status | rows |
| --- | ---: |
| delivered | 96,478 |
| shipped | 1,107 |
| canceled | 625 |
| unavailable | 609 |
| invoiced | 314 |
| processing | 301 |
| created | 5 |
| approved | 2 |

### Timestamp parseability

All five lifecycle timestamp columns parsed successfully in DEV:

- invalid purchase timestamps: `0`;
- invalid approval timestamps: `0`;
- invalid carrier timestamps: `0`;
- invalid customer-delivery timestamps: `0`;
- invalid estimated-delivery timestamps: `0`.

This supports typed Silver `TIMESTAMP` columns rather than preserving source strings.

### Timestamp nullability

| field | null rows |
| --- | ---: |
| order_purchase_timestamp | 0 |
| order_approved_at | 160 |
| order_delivered_carrier_date | 1,783 |
| order_delivered_customer_date | 2,965 |
| order_estimated_delivery_date | 0 |

The null profile confirms that purchase and estimated delivery are mandatory in the observed snapshot, while approval/carrier/customer-delivery are lifecycle-dependent nullable fields.

### Temporal-order observations

Observed violations of naive global timestamp sequencing:

- approval before purchase: `0`;
- carrier before approval: `1,359`;
- delivered before carrier: `23`;
- delivered before purchase: `0`.

Consequences:

1. `approved_at >= purchase_timestamp`, when approval exists, is supported by the observed DEV snapshot and is a candidate blocking invariant.
2. `delivered_customer_date >= purchase_timestamp`, when delivery exists, is supported by the observed DEV snapshot and is a candidate blocking invariant.
3. `carrier_date >= approved_at` is **not** a valid global blocking invariant because `1,359` rows violate it.
4. `delivered_customer_date >= carrier_date` is also **not** a safe global blocking invariant because `23` rows violate it.
5. The latter two relationships should be treated as observability/anomaly signals initially, or investigated by status/source semantics before promotion to blocking Data Quality rules.

## 5. Relationship model

Runtime-certified for the first slice:

```text
Customers(customer_id) 1 ---- 1 Orders(customer_id)   [current DEV snapshot]
```

Semantic contract for Silver remains:

```text
Customers(customer_id) 1 ---- N Orders(customer_id)
```

because `customer_id` is the transactional customer identifier and the model should not overfit the accidental one-order-per-customer-id cardinality of this static source snapshot.

Other relationships remain proposed until later profiling:

```text
Orders(order_id)              1 ---- N OrderItems(order_id)
Orders(order_id)              1 ---- N OrderPayments(order_id)
Orders(order_id)              1 ---- N OrderReviews(order_id)   [verify actual multiplicity]
Products(product_id)          1 ---- N OrderItems(product_id)
Sellers(seller_id)            1 ---- N OrderItems(seller_id)
ProductCategory(name)         1 ---- N Products(category_name)  [translation coverage may be partial]
MQL(mql_id)                   1 ---- 0..1 ClosedDeals(mql_id)   [verify]
Sellers(seller_id)            1 ---- 0..N ClosedDeals(seller_id) [verify]
```

Geolocation remains excluded from a naive 1:1 relationship. Its Bronze contract has no logical key and explicitly preserves repeated observations.

## 6. First Silver grains

### Customers

- Silver grain: one row per `customer_id`.
- key: `customer_id`.
- `customer_unique_id`: non-null longitudinal grouping attribute in the observed DEV source.
- geographic fields remain transaction-customer attributes at this stage.

### Orders

- Silver grain: one row per `order_id`.
- key: `order_id`.
- semantic foreign key: `customer_id` -> Silver Customers.
- zero observed DEV orphans.

### Later slices

- Order Items: (`order_id`, `order_item_id`).
- Payments: (`order_id`, `payment_sequential`).
- Reviews: initially (`review_id`, `order_id`) until runtime profiling proves simplification is safe.
- Products: `product_id`.
- Sellers: `seller_id`.
- Geography: not frozen.

## 7. Minimum temporal contract for Silver Orders

Proposed typed fields:

- `order_purchase_timestamp` -> `TIMESTAMP NOT NULL`;
- `order_approved_at` -> `TIMESTAMP NULL`;
- `order_delivered_carrier_date` -> `TIMESTAMP NULL`;
- `order_delivered_customer_date` -> `TIMESTAMP NULL`;
- `order_estimated_delivery_date` -> `TIMESTAMP NOT NULL`.

Candidate blocking rules supported by current evidence:

- non-null/unique `order_id`;
- non-null `customer_id`;
- referential integrity to Silver Customers;
- successful type conversion for all lifecycle timestamps;
- `order_approved_at >= order_purchase_timestamp` when approval exists;
- `order_delivered_customer_date >= order_purchase_timestamp` when customer delivery exists.

Candidate non-blocking/anomaly rules initially:

- carrier before approval;
- delivered before carrier;
- status-specific missing lifecycle timestamps;
- delivery after estimated date.

Status-specific lifecycle rules require a second, more detailed profile if we want them to become blocking invariants.

## 8. Data Quality implications

### Blocking for first vertical slice

Customers:

- `customer_id` non-null and unique;
- `customer_unique_id` non-null for the current accepted source contract;
- no forced uniqueness of `customer_unique_id`;
- no forced single-location constraint at longitudinal identity grain.

Orders:

- `order_id` non-null and unique;
- `customer_id` non-null;
- zero orphan Orders -> Customers;
- timestamp parse failures block the write;
- purchase/approval and purchase/delivery inversions can block where both timestamps exist.

### Do not block initially

- multiple `customer_id` per `customer_unique_id`;
- multiple customer locations per `customer_unique_id`;
- carrier-before-approval rows;
- delivered-before-carrier rows.

These are observed source semantics/anomalies, not proven invalid records.

## 9. Write semantics

For the first Silver slice, deterministic full-snapshot replacement remains the recommended persistence contract because:

- all upstream Olist Bronze datasets are current static `FULL_REPLACE` snapshots;
- no incremental source event semantics exist yet;
- no checkpoint/backfill requirement has been demonstrated;
- full rerun semantics are easy to explain and verify.

Do not introduce incremental processing, SCD semantics, MERGE-based change capture, or checkpoint infrastructure yet.

## 10. Initial conformed entities

Strong candidates:

- customer identity mapping (`customer_id` -> `customer_unique_id`);
- product category source/English enrichment after translation coverage profiling;
- geography only after dedicated ambiguity profiling.

Do not create yet:

- generic conformed date dimension;
- universal surrogate-key layer;
- generic entity framework;
- `SilverWriter`;
- generic SCD framework;
- generic incremental checkpoint framework.

## 11. Proposed Silver delivery order

### Slice 1

1. `silver.olist_customers`
2. `silver.olist_orders`
3. relationship Data Quality between Orders and Customers

### Slice 2

4. `silver.olist_products`
5. product category enrichment/translation
6. `silver.olist_sellers`
7. `silver.olist_order_items`
8. relationship DQ across order/product/seller

### Slice 3

9. `silver.olist_order_payments`
10. `silver.olist_order_reviews`

### Slice 4

11. conformed geography after dedicated profiling
12. enrich Customers/Sellers only after geographic grain is accepted

### Slice 5

13. `silver.olist_marketing_qualified_leads`
14. `silver.olist_closed_deals`

## 12. Minimum Silver architecture requirements for the next issue

The next architecture issue should define only what Customers + Orders require:

- explicit typed persisted schemas;
- explicit grains and keys;
- deterministic full-snapshot rerun semantics;
- source-to-Silver lineage sufficient for reproducibility;
- fail-fast incompatible schema drift;
- blocking/non-blocking Data Quality semantics;
- relationship DQ between Customers and Orders;
- deterministic handling of type-conversion failures;
- explicit metadata/contract boundaries;
- no generic Silver framework until repetition is demonstrated.

## 13. When a shared Silver abstraction becomes justified

A shared abstraction may be proposed only after at least two independently delivered Silver datasets demonstrate the same problem with materially equivalent semantics.

Minimum extraction criteria:

1. repeated code exists in at least two delivered Silver datasets;
2. the repeated behavior is stable after runtime evidence;
3. the behavior is technical/platform-like rather than source-specific business logic;
4. both consumers need the same failure/idempotency contract;
5. extraction reduces duplicated invariants rather than hiding important differences;
6. tests can express the shared contract independently of one dataset;
7. the abstraction does not force incremental/SCD/surrogate-key semantics on consumers that do not need them.

A `SilverWriter` remains explicitly deferred.

## 14. Decisions accepted

The following decisions are now accepted for the first Silver slice:

1. `customer_id` is the Silver Customers key/grain and Orders relationship key.
2. `customer_unique_id` is the longitudinal customer identity and is not globally unique per customer row.
3. Customer location remains attached to `customer_id`; it is not collapsed to one location per `customer_unique_id`.
4. Silver starts with Customers + Orders.
5. Orders lifecycle strings become typed timestamps.
6. Initial persistence is deterministic full-snapshot replacement.
7. A generic Silver writer/framework is not introduced in the first slice.
8. Geography grain remains unresolved until dedicated profiling.
9. Carrier-before-approval and delivered-before-carrier are not global blocking invariants.

## 15. Remaining discovery for later slices

Not required to begin Customers + Orders architecture, but required before later contracts freeze:

- Order Items -> Orders/Product/Seller orphan counts;
- Payments -> Orders orphan count;
- Reviews -> Orders orphan count and multiplicity distribution;
- Products -> Category Translation coverage;
- Closed Deals -> MQL/Seller coverage;
- Geolocation ambiguity per ZIP prefix;
- optional status-specific Orders timestamp/nullability profiling if stricter lifecycle DQ is desired.

## 16. Refined active backlog

1. **#101 — P0 Silver Discovery & Conformed Model** — complete after this evidence is accepted and merged.
2. **P0 Silver Contracts & Architecture** — next executable item.
3. **P0 Silver Customers + Orders vertical slice** — open after the minimum Silver architecture/contract is accepted.

Gold, incremental processing, features, ML, BI, additional orchestration, observability expansion and platform abstractions remain strategic backlog.
