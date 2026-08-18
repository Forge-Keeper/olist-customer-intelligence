from __future__ import annotations

from olist_data_platform.domains.ingestion.olist.customers_reader import (
    OlistCustomersReader,
)
from olist_data_platform.platform.delta.bronze.writer import BronzeWriter
from olist_data_platform.platform.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class OlistCustomersIngestionService:
    """Load the authoritative Olist customers snapshot into Bronze."""

    def __init__(
        self,
        reader: OlistCustomersReader,
        bronze_writer: BronzeWriter,
    ) -> None:
        self.reader = reader
        self.bronze_writer = bronze_writer

    def ingest(self) -> int:
        logger.info(
            "olist_customers_ingestion_started | source_path=%s | target_table=%s",
            self.reader.source_path,
            self.bronze_writer.target_table,
        )

        try:
            dataframe = self.reader.read()
            row_count = dataframe.count()

            logger.info(
                "olist_customers_snapshot_read | source_path=%s | row_count=%s | "
                "column_count=%s",
                self.reader.source_path,
                row_count,
                len(dataframe.columns),
            )

            self.bronze_writer.write(dataframe)

            logger.info(
                "olist_customers_ingestion_completed | target_table=%s | row_count=%s",
                self.bronze_writer.target_table,
                row_count,
            )
            return row_count

        except Exception:
            logger.exception(
                "olist_customers_ingestion_failed | source_path=%s | target_table=%s",
                self.reader.source_path,
                self.bronze_writer.target_table,
            )
            raise
