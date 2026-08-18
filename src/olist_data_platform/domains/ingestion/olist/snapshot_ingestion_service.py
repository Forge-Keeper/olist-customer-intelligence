from __future__ import annotations

from typing import Protocol

from pyspark.sql import DataFrame

from olist_data_platform.platform.delta.bronze.writer import BronzeWriter
from olist_data_platform.platform.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class SnapshotReader(Protocol):
    source_path: str

    def read(self) -> DataFrame: ...


class OlistSnapshotIngestionService:
    """Load an authoritative Olist snapshot into Bronze."""

    def __init__(
        self,
        dataset_name: str,
        reader: SnapshotReader,
        bronze_writer: BronzeWriter,
    ) -> None:
        if not dataset_name.strip():
            raise ValueError("dataset_name cannot be empty.")
        self.dataset_name = dataset_name
        self.reader = reader
        self.bronze_writer = bronze_writer

    def ingest(self) -> int:
        logger.info(
            "%s_ingestion_started | source_path=%s | target_table=%s",
            self.dataset_name,
            self.reader.source_path,
            self.bronze_writer.target_table,
        )
        try:
            dataframe = self.reader.read()
            row_count = dataframe.count()
            logger.info(
                "%s_snapshot_read | source_path=%s | row_count=%s | column_count=%s",
                self.dataset_name,
                self.reader.source_path,
                row_count,
                len(dataframe.columns),
            )
            self.bronze_writer.write(dataframe)
            logger.info(
                "%s_ingestion_completed | target_table=%s | row_count=%s",
                self.dataset_name,
                self.bronze_writer.target_table,
                row_count,
            )
            return row_count
        except Exception:
            logger.exception(
                "%s_ingestion_failed | source_path=%s | target_table=%s",
                self.dataset_name,
                self.reader.source_path,
                self.bronze_writer.target_table,
            )
            raise
