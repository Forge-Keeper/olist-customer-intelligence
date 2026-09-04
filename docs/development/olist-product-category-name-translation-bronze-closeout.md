# Olist Product Category Name Translation Bronze — Closeout

## Status

Final operational and deployment closeout for the Product Category Name Translation Bronze.

The vertical slice is complete across DEV, STG and PRD.

## Governed promotion path

```text
feature/olist-product-category-translation-bronze
  -> PR #66 -> dev
  -> PR #67 -> main
  -> Deploy STG
  -> human-authorized Deploy PRD
```

Stable production commit:

```text
20d995734f4c9f0d4bfab68fa8248940af041cec
```

## DEV acceptance

DEV acceptance was completed before promotion:

- production-like positive path succeeded against the canonical source;
- persisted target `dev.bronze.olist_product_category_name_translation` was validated;
- Control Plane lifecycle and DQ evidence were recorded;
- a controlled duplicate-key negative path was rejected by `CATEGORY-TRANSLATION-DQ03`;
- the rejected run wrote zero records and did not mutate the previously healthy target.

## STG evidence

Deploy STG run:

```text
33915255555
```

Result: `success`.

The workflow validated and deployed the staging bundle, ran deployment smokes, captured the promoted wheel manifest and retained the staging promotion artifact.

Retained STG artifact:

```text
stg-promotion-20d995734f4c9f0d4bfab68fa8248940af041cec
```

## PRD evidence

Human-authorized Deploy PRD run:

```text
33923138081
```

Result: `success`.

The workflow verified the approved STG artifact identity and digest, validated the production bundle, deployed the approved staging wheel, ran production deployment smokes and retained production deployment evidence.

Retained PRD artifact:

```text
prd-deployment-20d995734f4c9f0d4bfab68fa8248940af041cec
```

## Architecture boundary retained

The physical Products source contains two categories without translation in the observed mapping source:

```text
pc_gamer
portateis_cozinha_e_preparadores_de_alimentos
```

This remains intentionally deferred to Silver. It is not a Bronze validity defect and no Bronze cross-dataset DQ rule was introduced.

## Branch-lineage reconciliation

After the production deployment, the documentation closeout exposed a Git lineage issue caused by the earlier squash promotion from `dev` to `main`: file content was correct in `main`, but `dev` and `main` no longer shared the promoted feature commit as ancestry, causing a later `dev -> main` PR to re-expose already promoted implementation files.

The repository was reconciled by:

1. preserving the pre-reconciliation `dev` state under an archive branch;
2. closing the unsafe promotion PR without merge;
3. realigning `dev` to the current stable `main` commit;
4. reapplying this closeout documentation from the reconciled lineage through the normal topic-branch -> dev -> main governance path.

This closeout file is the authoritative final-state record for the feature. The earlier feature document contains the implementation/discovery detail and may still describe historical gate states from before final promotion.
