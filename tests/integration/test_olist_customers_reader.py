from pathlib import Path
from urllib.parse import urlparse

from pyspark.sql.types import StringType

from olist_data_platform.domains.ingestion.olist.customers_reader import (
    OlistCustomersReader,
)


def test_should_preserve_csv_values_as_strings_and_file_lineage(spark, tmp_path):
    source = Path(tmp_path) / "olist_customers_dataset.csv"
    source.write_text(
        "customer_id,customer_unique_id,customer_zip_code_prefix,customer_city,"
        "customer_state,new_source_column\n"
        "customer-1,unique-1,01151,sao paulo,SP,new-value\n",
        encoding="utf-8",
    )

    dataframe = OlistCustomersReader(spark, str(source)).read()
    row = dataframe.first()
    schema = {field.name: field.dataType for field in dataframe.schema.fields}

    assert row is not None
    assert row.customer_zip_code_prefix == "01151"
    assert row.new_source_column == "new-value"
    assert Path(urlparse(row.source_file).path).name == source.name
    assert isinstance(schema["customer_zip_code_prefix"], StringType)
    assert isinstance(schema["new_source_column"], StringType)
