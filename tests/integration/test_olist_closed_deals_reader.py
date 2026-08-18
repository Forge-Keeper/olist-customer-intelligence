from pathlib import Path

from pyspark.sql.types import StringType

from olist_data_platform.domains.ingestion.olist.csv_snapshot_reader import (
    OlistCsvSnapshotReader,
)
from olist_data_platform.jobs.olist_closed_deals_ingestion import (
    CLOSED_DEALS_SOURCE_COLUMNS,
)


def test_should_preserve_closed_deals_values_as_strings(spark, tmp_path):
    source = Path(tmp_path) / "olist_closed_deals_dataset.csv"
    source.write_text(
        "mql_id,seller_id,sdr_id,sr_id,won_date,business_segment,lead_type,"
        "lead_behaviour_profile,has_company,has_gtin,average_stock,business_type,"
        "declared_product_catalog_size,declared_monthly_revenue,extra_column\n"
        "mql-1,seller-1,sdr-1,sr-1,2018-01-01,retail,online,cat,TRUE,FALSE,10,"
        "reseller,20,1000,extra\n",
        encoding="utf-8",
    )

    dataframe = OlistCsvSnapshotReader(
        spark=spark,
        source_path=str(source),
        required_columns=CLOSED_DEALS_SOURCE_COLUMNS,
        dataset_name="olist_closed_deals",
    ).read()
    row = dataframe.first()
    schema = {field.name: field.dataType for field in dataframe.schema.fields}

    assert row is not None
    assert row.declared_monthly_revenue == "1000"
    assert row.extra_column == "extra"
    assert isinstance(schema["declared_monthly_revenue"], StringType)
    assert isinstance(schema["won_date"], StringType)
