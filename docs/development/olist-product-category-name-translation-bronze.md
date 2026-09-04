# Olist Product Category Name Translation Bronze

## Scope

This feature adds the Product Category Name Translation Bronze slice for the physical source file:

```text
product_category_name_translation.csv
```

The feature follows the existing Olist CSV snapshot ingestion architecture and preserves source values without normalization or translation logic in Bronze.

## Gate status

- Discovery: complete.
- Requirements: next.
- Technical Design: pending.
- Impact Analysis: pending.
- Implementation Plan: pending.
- Implementation: pending.
- DEV Validation: pending.
- STG: pending.
- PRD: pending.
- Closeout: pending.

## Discovery evidence

Discovery was executed read-only against the physical DEV source:

```text
path=dbfs:/Volumes/dev/bronze/raw_storage/raw/olist/e_commerce/product_category_name_translation.csv
name=product_category_name_translation.csv
row_count=71
size_bytes=2613
column_count=2
```

Observed schema:

```text
product_category_name:string
product_category_name_english:string
```

No schema inference, normalization, source mutation, caching or persistence was used during discovery.

### Candidate grain

`product_category_name` is complete and unique in the observed snapshot:

```text
distinct_count=71
null_count=0
blank_count=0
duplicate_group_count=0
duplicate_row_excess=0
```

No exact duplicate rows were observed:

```text
duplicate_group_count=0
duplicate_row_excess=0
```

Observed candidate grain: one row per `product_category_name`.

This remains a discovery-supported candidate until Requirements formally accept it as the Bronze logical key.

### Completeness and lexical shape

Both source columns are complete in the observed snapshot:

| Column | Nulls | Blanks | Distinct raw | Distinct trim/lower | Trim differences |
|---|---:|---:|---:|---:|---:|
| `product_category_name` | 0 | 0 | 71 | 71 | 0 |
| `product_category_name_english` | 0 | 0 | 71 | 71 | 0 |

No basic mojibake/replacement markers were detected in either column:

```text
product_category_name encoding_suspect_rows=0
product_category_name_english encoding_suspect_rows=0
```

### Deterministic content signature

```text
row_count=71
distinct_row_hashes=71
row_hash_sum=24255282855097946299
```

### Relationship to Products

Discovery compared the translation source with the physical DEV Products source:

```text
products_path=dbfs:/Volumes/dev/bronze/raw_storage/raw/olist/e_commerce/olist_products_dataset.csv
products_row_count=32951
products_distinct_non_null_categories=73
translation_distinct_categories=71
```

Two Products categories have no translation in the translation snapshot:

```text
pc_gamer
portateis_cozinha_e_preparadores_de_alimentos
```

No translation categories were observed that are unused by Products:

```text
translations_not_used_by_products_count=0
```

This revalidates the historical Products discovery evidence. It does not by itself establish a Bronze blocking cross-dataset foreign-key rule.

### Snapshot semantics

Only one physical CSV snapshot was observed. Discovery found no business date or refresh-cadence evidence in the source itself.

Therefore Discovery does not support introducing:

- `dt_base`;
- inferred incremental cadence;
- partitioning by business date;
- clustering based on cadence assumptions.

## Discovery-supported conclusions

The current evidence supports the following inputs to Requirements:

1. Physical source name is `product_category_name_translation.csv`.
2. Physical source has exactly two string columns.
3. One row per `product_category_name` is supported as the candidate grain.
4. Both columns are complete in the observed snapshot.
5. `product_category_name` is unique in the observed snapshot.
6. Source values show no trim/case cardinality collapse and no basic encoding anomalies.
7. Translation coverage is incomplete relative to Products: 2 of 73 observed Products categories have no translation.
8. There are no translation-only categories relative to the observed Products snapshot.
9. Cross-dataset coverage must be treated explicitly in Requirements/Design rather than silently converted into a Bronze rejection rule.
10. No source cadence, `dt_base`, partitioning or clustering assumption is evidenced.

## Risks carried into Requirements

- Future duplicate or missing `product_category_name` rows could make the translation mapping ambiguous.
- Future missing `product_category_name_english` values could reduce translation usability downstream.
- The source is not referentially complete relative to Products; making that relationship blocking in Bronze would reject a source snapshot that is currently known to be physically valid but incomplete for downstream translation.
- Source-shape drift could introduce additional/missing columns or lexical anomalies.

## Open questions for Requirements

1. Should `product_category_name` be formally accepted as the logical Bronze key?
2. Should completeness of `product_category_name_english` be blocking in Bronze, given 0 missing values observed and the file's sole purpose as a translation mapping?
3. Should translation coverage relative to Products remain non-blocking observational evidence, consistent with source-faithful Bronze boundaries?
4. Should the write strategy remain `FULL_REPLACE`, consistent with the static Olist snapshot pattern?

No production implementation is authorized before Requirements, Technical Design and Impact Analysis are closed.
