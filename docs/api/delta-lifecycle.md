# Delta Table Lifecycle

`DeltaTableLifecycle` owns the external Delta/Unity Catalog table state for a `DatasetContract`.
It is intentionally separate from `BronzeWriter`, which owns write semantics such as MERGE,
FULL_REPLACE and replaceWhere.

::: olist_data_platform.platform.delta.lifecycle.DeltaTableLifecycle

::: olist_data_platform.platform.delta.lifecycle.SchemaDiff

::: olist_data_platform.platform.delta.lifecycle.TypeMismatch
