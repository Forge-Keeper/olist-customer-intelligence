from pathlib import Path

from pyspark.sql.types import StringType

from olist_data_platform.domains.ingestion.olist.csv_snapshot_reader import (
    OlistCsvSnapshotReader,
)
from olist_data_platform.jobs.olist_marketing_qualified_leads_ingestion import (
    MQL_SOURCE_COLUMNS,
)


def test_should_preserve_mql_values_as_strings_and_source_nulls(spark, tmp_path):
    source = Path(tmp_path) / "olist_marketing_qualified_leads_dataset.csv"
    source.write_text(
        "mql_id,first_contact_date,landing_page_id,origin,extra_column\n"
        "mql-1,2018-02-01,landing-1,social,extra\n"
        "mql-2,2018-02-02,landing-2,,extra-2\n",
        encoding="utf-8",
    )

    dataframe = OlistCsvSnapshotReader(
        spark=spark,
        source_path=str(source),
        required_columns=MQL_SOURCE_COLUMNS,
        dataset_name="olist_marketing_qualified_leads",
    ).read()
    rows = dataframe.orderBy("mql_id").collect()
    schema = {field.name: field.dataType for field in dataframe.schema.fields}

    assert rows[0].first_contact_date == "2018-02-01"
    assert rows[0].extra_column == "extra"
    assert rows[1].origin is None
    assert isinstance(schema["first_contact_date"], StringType)
    assert isinstance(schema["origin"], StringType)
