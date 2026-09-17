from unittest.mock import Mock

from pyspark.sql.types import StringType, StructField, StructType

from olist_data_platform.platform.delta import (
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.lifecycle import DeltaTableLifecycle


def test_ensure_can_validate_existing_table_without_metadata_reconciliation() -> None:
    spark = Mock()
    spark.catalog.tableExists.return_value = True
    spark.table.return_value.schema = StructType(
        [StructField("id", StringType(), False)]
    )
    spark.sql.return_value.collect.return_value = [
        {"partitionColumns": [], "clusteringColumns": []}
    ]
    contract = DatasetContract(
        columns=(
            ColumnContract(
                "id",
                "string",
                False,
                "Identifier.",
            ),
        ),
        key_columns=("id",),
        metadata=TableMetadata(
            description="Runtime control table.",
            tags={"managed_by": "olist_data_platform"},
        ),
    )
    lifecycle = DeltaTableLifecycle(
        spark,
        "dev_admin.operations.execution_runs",
        contract,
    )

    lifecycle.ensure(reconcile_metadata=False)

    sql_calls = [call.args[0] for call in spark.sql.call_args_list]
    assert any("DESCRIBE DETAIL" in sql for sql in sql_calls)
    assert not any("COMMENT ON TABLE" in sql for sql in sql_calls)
    assert not any("ALTER COLUMN" in sql for sql in sql_calls)
    assert not any("SET TAGS" in sql for sql in sql_calls)
