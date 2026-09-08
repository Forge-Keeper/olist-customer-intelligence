# Olist Order Reviews Bronze

`olist_order_reviews` lands the authoritative Olist order-reviews CSV snapshot into Bronze without business transformation.

## Discovery evidence

The physical DEV source is:

`/Volumes/dev/bronze/raw_storage/raw/olist/e_commerce/olist_order_reviews_dataset.csv`

Read-only discovery established:

- 99,224 source rows;
- physical columns: `review_id`, `order_id`, `review_score`, `review_comment_title`, `review_comment_message`, `review_creation_date`, `review_answer_timestamp`;
- no exact full-row duplicates;
- no single source column is both complete and unique;
- `review_id` has 98,410 distinct values, 789 duplicate groups and maximum multiplicity 3;
- `order_id` has 98,673 distinct values, 547 duplicate groups and maximum multiplicity 3;
- `(review_id, order_id)` is complete and unique across all 99,224 rows;
- `(order_id, review_answer_timestamp)` is also unique in this snapshot, but is not selected as the natural key because the answer timestamp is an event attribute rather than an identifier;
- `review_score` is complete, integer-shaped and currently observes only values 1 through 5; that observed distribution is not promoted into a Bronze enum/domain constraint;
- `review_creation_date` and `review_answer_timestamp` are complete and 100% timestamp-parseable;
- `review_comment_title` is optional: 87,656 nulls, 2 non-null blanks and 1,998 rows whose source whitespace would change under trim;
- `review_comment_message` is optional: 58,247 nulls, 9 non-null blanks and 8,120 rows whose source whitespace would change under trim;
- all 98,673 distinct source `order_id` values are present in the sibling Orders snapshot. This is observational relationship evidence only and is not a Bronze FK gate.

The source contains free-text review content. Discovery therefore uses multiline CSV parsing with quote escaping so embedded line breaks remain part of the source field rather than being interpreted as physical records.

## Bronze contract

The persisted source columns remain strings. Bronze does not trim, normalize, translate, infer sentiment, or coerce source values into analytical types.

Natural key:

```text
(review_id, order_id)
```

Write strategy:

```text
FULL_REPLACE
```

The source is treated as an authoritative snapshot. A successful rerun must reproduce the same semantic snapshot rather than append duplicate records.

### Nullability

Required source attributes:

- `review_id`;
- `order_id`;
- `review_score`;
- `review_creation_date`;
- `review_answer_timestamp`.

Optional source attributes:

- `review_comment_title`;
- `review_comment_message`.

`source_file` and `ingestion_timestamp` provide technical lineage.

## Data Quality policy

### Blocking `ERROR`

- source snapshot is non-empty;
- composite natural key is complete;
- composite natural key is unique;
- required non-key attributes are non-null;
- `review_score` remains integer-shaped;
- `review_creation_date` remains timestamp-parseable;
- `review_answer_timestamp` remains timestamp-parseable.

### Observational `INFO`

The quality contract records counts for:

- null review titles;
- null review messages;
- non-null blank titles;
- non-null blank messages;
- title whitespace that would change under trimming;
- message whitespace that would change under trimming.

These observations do not block ingestion. They document source characteristics that Bronze intentionally preserves.

## Non-goals

This slice does **not**:

- enforce Orders as a cross-dataset foreign key;
- require one review per order or one order per review identifier;
- enforce the currently observed `review_score` values as a closed enum;
- trim or normalize review text;
- remove blank review text;
- convert persisted timestamps or scores into typed analytical columns;
- deduplicate source records beyond rejecting duplicate natural keys;
- perform sentiment analysis, text cleaning, language detection or moderation;
- reconcile review chronology with order lifecycle events.

Those concerns belong to downstream modeling or separately approved requirements.

## Runtime composition

```text
OlistCsvSnapshotReader (multiline CSV)
  -> OlistSnapshotIngestionService
     -> DataQualityRunner / QualityResultWriter
     -> BronzeWriter.write_checked()
        -> FULL_REPLACE Delta snapshot
```

The reusable Olist CSV reader keeps its previous single-line behavior by default; Order Reviews opts into multiline parsing explicitly because free-text comments require it.

## Runtime acceptance

DEV bundle deployment completed successfully from feature head `0be0263265cd7c7226dac0b66d35093b661cadb1`.

First runtime execution:

- Databricks job ID: `798901500146387`;
- Databricks run ID: `632748785950044`;
- application run ID: `f6e12a5b-5cd1-4311-8e99-7dd51332d35a`;
- terminal state: `SUCCESS`;
- source rows read: 99,224;
- Bronze rows written: 99,224;
- target: `dev.bronze.olist_order_reviews`.

Second runtime execution against the same source snapshot:

- Databricks job ID: `798901500146387`;
- Databricks run ID: `325597771545425`;
- application run ID: `d4be7a36-6565-4bc5-b296-250704c6ba9b`;
- terminal state: `SUCCESS`;
- source rows read: 99,224;
- Bronze rows written: 99,224;
- target: `dev.bronze.olist_order_reviews`.

Post-rerun integrity checks on `dev.bronze.olist_order_reviews` confirmed:

- `row_count = 99224`;
- `distinct_key_count = 99224` for `(review_id, order_id)`;
- `null_key_rows = 0`;
- `null_source_file_rows = 0`;
- `null_ingestion_timestamp_rows = 0`.

The repeated successful `FULL_REPLACE` execution plus the post-rerun integrity checks provide runtime evidence for semantic idempotence and complete technical lineage in DEV.
