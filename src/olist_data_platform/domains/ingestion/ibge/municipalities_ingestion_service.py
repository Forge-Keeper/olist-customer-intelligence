from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any, Protocol
from uuid import uuid4

from olist_data_platform.domains.ingestion.ibge.municipalities_extractor import (
    MunicipalitiesExtractor,
)
from olist_data_platform.platform.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class MunicipalitiesClient(Protocol):
    def get_municipalities(self) -> list[dict[str, Any]]: ...


class MunicipalitiesWriter(Protocol):
    def write(self, records: list[dict[str, Any]], request_id: str) -> None: ...


class MunicipalitiesIngestionService:
    def __init__(
        self,
        client: MunicipalitiesClient,
        bronze_writer: MunicipalitiesWriter,
        request_id_factory: Callable[[], str] | None = None,
        snapshot_date_factory: Callable[[], date] | None = None,
    ) -> None:
        self.client = client
        self.bronze_writer = bronze_writer
        self.request_id_factory = request_id_factory or (lambda: str(uuid4()))
        self.snapshot_date_factory = snapshot_date_factory or date.today

    def ingest(self) -> str:
        request_id = self.request_id_factory()
        snapshot_date = self.snapshot_date_factory()
        logger.info(
            "ibge_municipalities_ingestion_started | request_id=%s | snapshot_date=%s",
            request_id,
            snapshot_date,
        )
        try:
            payload = self.client.get_municipalities()
            records = MunicipalitiesExtractor.extract(
                payload,
                snapshot_date=snapshot_date,
            )
            if not records:
                raise ValueError("IBGE municipalities ingestion returned no records.")
            self.bronze_writer.write(records, request_id)
            logger.info(
                "ibge_municipalities_ingestion_completed | "
                "request_id=%s | snapshot_date=%s | record_count=%s",
                request_id,
                snapshot_date,
                len(records),
            )
            return request_id
        except Exception:
            logger.exception(
                "ibge_municipalities_ingestion_failed | "
                "request_id=%s | snapshot_date=%s",
                request_id,
                snapshot_date,
            )
            raise
