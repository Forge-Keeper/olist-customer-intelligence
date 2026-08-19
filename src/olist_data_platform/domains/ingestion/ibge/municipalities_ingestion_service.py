from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from olist_data_platform.domains.bronze.ibge.bronze_municipalities_writer import (
    BronzeMunicipalitiesWriter,
)
from olist_data_platform.domains.ingestion.ibge.localities_client import LocalitiesClient
from olist_data_platform.domains.ingestion.ibge.municipalities_extractor import (
    MunicipalitiesExtractor,
)
from olist_data_platform.platform.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class MunicipalitiesIngestionService:
    def __init__(
        self,
        client: LocalitiesClient,
        bronze_writer: BronzeMunicipalitiesWriter,
        request_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.client = client
        self.bronze_writer = bronze_writer
        self.request_id_factory = request_id_factory or (lambda: str(uuid4()))

    def ingest(self) -> str:
        request_id = self.request_id_factory()
        logger.info("ibge_municipalities_ingestion_started | request_id=%s", request_id)
        try:
            payload = self.client.get_municipalities()
            records = MunicipalitiesExtractor.extract(payload)
            if not records:
                raise ValueError("IBGE municipalities ingestion returned no records.")
            self.bronze_writer.write(records, request_id)
            logger.info(
                "ibge_municipalities_ingestion_completed | request_id=%s | record_count=%s",
                request_id,
                len(records),
            )
            return request_id
        except Exception:
            logger.exception("ibge_municipalities_ingestion_failed | request_id=%s", request_id)
            raise
