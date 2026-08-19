from __future__ import annotations

from collections.abc import Callable
from uuid import uuid4

from olist_data_platform.domains.bronze.ibge.bronze_municipality_population_writer import (
    BronzeMunicipalityPopulationWriter,
)
from olist_data_platform.domains.ingestion.ibge.datasets import MUNICIPALITY_POPULATION
from olist_data_platform.domains.ingestion.ibge.municipality_population_extractor import (
    MunicipalityPopulationExtractor,
)
from olist_data_platform.domains.ingestion.ibge.sidra_client import SidraClient
from olist_data_platform.domains.ingestion.ibge.sidra_parser import SidraParser
from olist_data_platform.platform.logging import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class MunicipalityPopulationIngestionService:
    def __init__(
        self,
        client: SidraClient,
        bronze_writer: BronzeMunicipalityPopulationWriter,
        request_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.client = client
        self.bronze_writer = bronze_writer
        self.request_id_factory = request_id_factory or (lambda: str(uuid4()))

    def ingest(self, periods: tuple[str, ...] = ("2016", "2017", "2018")) -> str:
        request_id = self.request_id_factory()
        logger.info(
            "ibge_population_ingestion_started | request_id=%s | periods=%s",
            request_id,
            periods,
        )
        try:
            query = MUNICIPALITY_POPULATION.build_query(
                territories="all",
                periods=periods,
            )
            payload = self.client.get_values(query)
            decoded = SidraParser.decode(payload)
            records = MunicipalityPopulationExtractor.extract(decoded)
            if not records:
                raise ValueError("IBGE population ingestion returned no records.")
            self.bronze_writer.write(records, request_id)
            logger.info(
                "ibge_population_ingestion_completed | request_id=%s | record_count=%s",
                request_id,
                len(records),
            )
            return request_id
        except Exception:
            logger.exception(
                "ibge_population_ingestion_failed | request_id=%s | periods=%s",
                request_id,
                periods,
            )
            raise
