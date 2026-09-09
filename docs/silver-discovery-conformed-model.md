# Silver Discovery & Conformed Model

Status: discovery proposal for review  
Tracking: GitHub Issue #101  
Scope: Olist analytical Silver only; no transformation implementation in this change.

## 1. Evidence boundary

This document separates three evidence levels:

- **Repository fact**: directly declared by `main` contracts, code, or canonical Platform Status.
- **Accepted runtime fact**: execution evidence already normalized into canonical project documentation.
- **Proposed model**: analytical interpretation that still requires review and, where noted, Databricks profiling before contract freeze.

Bronze remains source-faithful. Silver is responsible for typing, harmonization, conformance, explicit relationship semantics, and quality rules justified by the analytical model.

No runtime cardinality, orphan rate, uniqueness claim, or distribution is asserted here unless already recorded as accepted evidence.

## 2. Current Olist Bronze inventory

`main` currently contains code for the complete 11-source public Olist CSV boundary.

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

## 3. Customer identity

### Repository facts

`bronze.olist_customers` declares:

- `customer_id` as the dataset key and non-null;
- `customer_unique_id` as a separate nullable source field;
- geographic attributes tied to the `customer_id` row.

`bronze.olist_orders` stores `customer_id`, not `customer_unique_id`.

### Proposed semantic model

Silver should preserve both concepts explicitly:

- **`customer_id`**: transactional/source customer identifier used by Orders. It is the correct direct join key from Orders to Customers.
- **`customer_unique_id`**: longitudinal customer identity candidate used to group multiple transactional customer records that belong to the same underlying customer.

Therefore, the first Silver design should not replace `customer_id` with `customer_unique_id` and should not make Orders directly reference `customer_unique_id` without passing through the customer mapping.

Proposed first model:

```text
silver.customers
  customer_id                 -- source transactional identifier
  customer_unique_id          -- longitudinal identity candidate
  customer_zip_code_prefix
  customer_city
  customer_state
  ...typed/conformed fields

silver.orders
  order_id
  customer_id                 -- FK semantic to silver.customers.customer_id
  ...typed lifecycle fields
```

A later consumer such as Customer 360 may group by `customer_unique_id`, but that is a downstream semantic choice rather than a reason to erase `customer_id` in Silver.

### Runtime evidence still required

Before freezing the customer identity contract:

1. count distinct/non-null `customer_id`;
2. count distinct/non-null `customer_unique_id`;
3. distribution of number of `customer_id` values per `customer_unique_id`;
4. verify whether any `customer_unique_id` maps to contradictory state/city/ZIP values and whether those differences are legitimate transaction-time addresses;
5. orphan rate from Orders to Customers by `customer_id`.

## 4. Relationship model and expected cardinalities

The following cardinalities are **proposed from source semantics and declared keys**. They are not runtime-certified until profiling is executed.

```text
Customers(customer_id)        1 ---- N Orders(customer_id)
Orders(order_id)              1 ---- N OrderItems(order_id)
Orders(order_id)              1 ---- N OrderPayments(order_id)
Orders(order_id)              1 ---- N OrderReviews(order_id)   [verify actual multiplicity]
Products(product_id)          1 ---- N OrderItems(product_id)
Sellers(seller_id)            1 ---- N OrderItems(seller_id)
ProductCategory(name)         1 ---- N Products(category_name)  [translation coverage may be partial]
MQL(mql_id)                   1 ---- 0..1 ClosedDeals(mql_id)   [verify]
Sellers(seller_id)            1 ---- 0..N ClosedDeals(seller_id) [verify]
```

Geolocation is deliberately excluded from a naive 1:1 relationship. Its Bronze contract has no logical key and explicitly preserves repeated observations. A conformed geographic entity must therefore be derived from an observed rule rather than by assuming `zip_code_prefix` is unique.

## 5. Natural/business keys and grains

### Customers

- Bronze grain: source customer row.
- Declared key: `customer_id`.
- Longitudinal grouping candidate: `customer_unique_id`.
- Silver grain proposal: one row per `customer_id`.

Reason: this preserves the key referenced by Orders while retaining the longitudinal identifier for downstream grouping.

### Orders

- Bronze grain: one order.
- Declared key: `order_id`.
- Silver grain proposal: one row per `order_id`.

### Order Items

- Bronze grain: item sequence within an order.
- Declared key: (`order_id`, `order_item_id`).
- Silver grain proposal: same.

`order_item_id` is not treated as globally unique.

### Payments

- Bronze grain: payment sequence within an order.
- Declared key: (`order_id`, `payment_sequential`).
- Silver grain proposal: same.

Aggregated payment totals belong to a downstream dataset/product unless a concrete Silver consumer proves they are a stable reusable semantic entity.

### Reviews

- Bronze grain/key: (`review_id`, `order_id`).
- Silver grain proposal: preserve that key initially.

Do not assume `review_id` alone is unique until runtime profiling verifies it.

### Products

- Bronze grain: product.
- Declared key: `product_id`.
- Silver grain proposal: one row per `product_id` with typed numeric measures and category enrichment.

### Sellers

- Bronze grain: seller.
- Declared key: `seller_id`.
- Silver grain proposal: one row per `seller_id`.

### Product Category Translation

- Bronze grain/key: one row per Portuguese `product_category_name`.
- Silver role: conform category labels used by Products.

Translation coverage must be measured. Missing translations should not reject a valid product row by default; the product category can remain available in its source language with nullable English enrichment unless a consumer requires otherwise.

### Geolocation

- Bronze grain: raw observation.
- Declared key: none.
- Silver grain: **not yet frozen**.

Candidate conformed grains to evaluate through profiling:

1. one row per ZIP prefix;
2. one row per (`zip_code_prefix`, city, state);
3. canonical ZIP-prefix row plus retained observation statistics;
4. separate geographic conformed entity derived from a deterministic representative-location rule.

No option should be selected before measuring ambiguity and duplication.

### Marketing Qualified Leads / Closed Deals

These form a separate seller-acquisition funnel rather than the core order/customer analytical slice.

- MQL declared key: `mql_id`.
- Closed Deals declared key: `mql_id`.
- Closed Deals optionally references `seller_id`.

They should remain out of the first Customers + Orders Silver slice unless an immediate consumer requires seller acquisition analysis.

## 6. Temporal semantics

Bronze preserves timestamps/dates as strings. Silver should introduce explicit temporal types and lifecycle validation.

### Orders

Candidate typed fields:

- `order_purchase_timestamp` -> timestamp, required;
- `order_approved_at` -> timestamp, nullable;
- `order_delivered_carrier_date` -> timestamp, nullable;
- `order_delivered_customer_date` -> timestamp, nullable;
- `order_estimated_delivery_date` -> timestamp, required.

Proposed quality checks must account for order status. A globally strict sequence such as `purchase <= approval <= carrier <= customer` may be invalid for cancelled/unavailable orders because later lifecycle timestamps may legitimately be null.

Required profiling before freezing rules:

- status distribution;
- nullability by status for every lifecycle timestamp;
- count and sample of timestamp-order inversions;
- estimated-vs-actual delivery behavior.

### Reviews

- `review_creation_date` -> date/timestamp according to observed source precision;
- `review_answer_timestamp` -> timestamp;
- proposed invariant: answer should not precede creation, subject to source-profile verification.

### Marketing funnel

- `first_contact_date` and `won_date` should be typed;
- candidate invariant: `won_date >= first_contact_date` when both exist, but only after confirming one-to-one MQL/closed-deal semantics.

## 7. Integrity and data-quality risks

### P0 risks for first vertical slice

1. **Customer identity collapse**: using `customer_unique_id` as the direct Orders foreign key would change source relationship semantics.
2. **Unverified orphan assumptions**: declared join fields do not prove referential completeness.
3. **Timestamp typing failures**: Bronze strings may contain unexpected values that require explicit reject/quarantine semantics.
4. **Status-dependent lifecycle rules**: over-strict temporal checks could reject legitimate cancelled/unavailable orders.
5. **Technical lineage loss**: Silver should retain sufficient traceability to explain the Bronze source/rerun that produced a row, but should not blindly duplicate every Bronze technical column without a defined lineage contract.

### Later-slice risks

6. product-category translation coverage may be incomplete;
7. geolocation has repeated observations and no Bronze key;
8. payment sums may differ from item+freight totals for legitimate or anomalous reasons and require measured tolerances/semantics;
9. reviews may not have simple one-review-per-order multiplicity;
10. nullable Closed Deals `seller_id` may represent funnel semantics that should not be forced into a strict referential constraint.

## 8. Candidate conformed entities

The following are candidates, not automatic abstractions.

### Strong candidates

- **Customer identity mapping**: `customer_id` -> `customer_unique_id` semantics are required by multiple future customer analyses.
- **Product category**: source category + English translation can become a stable conformed attribute once translation coverage is profiled.
- **Geography**: likely shared by customers and sellers, but grain/canonicalization is unresolved and requires profiling first.

### Do not create yet

- generic conformed date dimension;
- generalized entity framework;
- universal surrogate-key layer;
- `SilverWriter`;
- generic SCD framework;
- generic incremental checkpoint framework.

None is justified by the current discovery evidence.

## 9. Proposed Silver dataset order

### Slice 1 — minimum vertical slice

1. `silver.olist_customers`
2. `silver.olist_orders`
3. relationship Data Quality between Orders and Customers

Purpose: discover the real Silver contract, typing, lineage, write and DQ needs with the smallest end-to-end relationship that also forces the customer identity decision.

### Slice 2 — commerce line model

4. `silver.olist_products`
5. product category enrichment/translation
6. `silver.olist_sellers`
7. `silver.olist_order_items`
8. relationship DQ across order/product/seller

### Slice 3 — order outcomes

9. `silver.olist_order_payments`
10. `silver.olist_order_reviews`

### Slice 4 — geography

11. conformed geography after dedicated profiling of repeated observations
12. enrich Customers/Sellers only after the geographic grain is accepted

### Slice 5 — seller acquisition funnel

13. `silver.olist_marketing_qualified_leads`
14. `silver.olist_closed_deals`

This ordering keeps the first Silver work focused on Customer Intelligence while avoiding premature coupling to seller acquisition and unresolved geography semantics.

## 10. Proposed Silver contract minimum

The next architecture issue should define only the minimum contract needed by Customers + Orders. Candidate requirements:

- explicit persisted schema with typed business columns;
- explicit grain and key columns;
- deterministic full-snapshot rerun semantics initially;
- source-to-Silver lineage metadata sufficient for reproducibility;
- fail-fast incompatible schema drift;
- pre-write Data Quality for key/null/type failures;
- post-transform relationship checks where practical;
- clear separation of blocking vs non-blocking DQ;
- explicit handling of rejected/invalid typed values;
- no implicit incremental behavior until incremental requirements exist.

Full reload is the safest initial write semantic because the upstream Olist sources are static snapshots and all current Olist Bronze contracts are `FULL_REPLACE`. Incrementality should not be invented before a real requirement demonstrates value.

## 11. Runtime profiling required before contract freeze

The following Databricks queries/evidence should be captured against the accepted DEV Bronze state.

### Customers / identity

- row count;
- distinct `customer_id`;
- null `customer_id`;
- distinct/null `customer_unique_id`;
- count distribution of `customer_id` per `customer_unique_id`;
- conflicting geography across one `customer_unique_id`.

### Orders

- row count and distinct `order_id`;
- orphan `customer_id` count/rate;
- status distribution;
- timestamp parse success rates;
- timestamp nullability by status;
- lifecycle-order violation counts.

### Relationship baseline for later slices

- Order Items -> Orders/Product/Seller orphan counts;
- Payments -> Orders orphan count;
- Reviews -> Orders orphan count and multiplicity distribution;
- Products -> Category Translation coverage;
- Closed Deals -> MQL/Seller coverage;
- Geolocation ambiguity per ZIP prefix.

These results should be persisted as discovery evidence, not merely copied into chat, so later Silver decisions remain reproducible.

## 12. When a shared Silver abstraction becomes justified

A shared abstraction may be proposed only after at least two independent Silver datasets demonstrate the same problem with materially equivalent semantics.

Minimum extraction criteria:

1. repeated code exists in at least two delivered Silver datasets;
2. the repeated behavior is stable after runtime evidence;
3. the behavior is technical/platform-like rather than source-specific business logic;
4. both consumers need the same failure/idempotency contract;
5. extraction reduces duplicated invariants rather than hiding important differences;
6. tests can express the shared contract independently of one dataset;
7. the abstraction does not force incremental/SCD/surrogate-key semantics on consumers that do not need them.

Examples that may eventually qualify:

- common typed-snapshot write lifecycle;
- shared Silver lineage columns;
- repeated checked-write integration with Data Quality;
- common safe replacement semantics.

A `SilverWriter` is therefore explicitly deferred until repetition is demonstrated by real Silver implementations.

## 13. Decisions proposed for human review

1. Keep `customer_id` as the Silver Customers grain/key and Orders relationship key.
2. Preserve `customer_unique_id` as the longitudinal customer identifier, not as a replacement for `customer_id`.
3. Start Silver with `customers + orders` only.
4. Use deterministic full-snapshot replacement for the first slice unless discovery exposes a reason not to.
5. Do not create a shared Silver writer/framework in the first slice.
6. Do not freeze a conformed geography grain until runtime ambiguity is profiled.
7. Treat relationship cardinalities in this document as proposed until DEV profiling certifies them.

## 14. Open questions

- What is the observed multiplicity of `customer_id` per `customer_unique_id`?
- Do customer address fields vary materially within a `customer_unique_id`, and should Silver model those as transaction-time attributes rather than a single canonical customer address?
- Are all Orders `customer_id` values present in Customers?
- Which order lifecycle timestamp rules remain valid for each `order_status`?
- Is (`review_id`, `order_id`) necessary in Silver, or can runtime evidence prove a simpler stable key?
- What deterministic rule, if any, can produce a canonical geography record per ZIP prefix without destroying useful source variation?

## 15. Refined active backlog

Keep the executable queue small:

1. **#101 — P0 Silver Discovery & Conformed Model** — this document + runtime profiling evidence.
2. **P0 Silver Contracts & Architecture** — open only after the decisions above are accepted and profiling closes P0 unknowns.
3. **P0 Silver Customers + Orders vertical slice** — open after the minimum Silver contract is accepted.

Gold, incremental processing, features, ML, BI, additional orchestration, observability expansion and platform abstractions remain strategic backlog and should not be expanded into dozens of executable issues yet.

## 16. Next concrete step / gate

The repository-only discovery is sufficient to propose the model, but it is not sufficient to certify runtime cardinalities and referential integrity.

**Next step:** execute the DEV Bronze profiling listed in section 11, capture the evidence, then freeze the customer identity and Customers/Orders relationship decisions.

**Human gate:** approve or change the proposed customer identity semantics and first-slice boundary after reviewing this discovery and the DEV profiling evidence. That decision changes Silver grain/contract semantics and should not be made implicitly.
