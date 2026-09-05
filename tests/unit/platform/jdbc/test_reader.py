from unittest.mock import MagicMock

from olist_data_platform.platform.jdbc import JdbcConfig, JdbcReader


def test_jdbc_reader_delegates_to_spark_jdbc_options() -> None:
    spark = MagicMock()
    configured_reader = spark.read.format.return_value.options.return_value
    expected_dataframe = object()
    configured_reader.load.return_value = expected_dataframe

    config = JdbcConfig(
        host="db.example.com",
        port=5432,
        database="olist",
        user="reader",
        password="secret",
    )
    reader = JdbcReader(spark=spark, config=config)

    result = reader.read_table("anp.combustiveis_precos")

    spark.read.format.assert_called_once_with("jdbc")
    spark.read.format.return_value.options.assert_called_once_with(
        **config.options,
        dbtable="anp.combustiveis_precos",
    )
    configured_reader.load.assert_called_once_with()
    assert result is expected_dataframe
