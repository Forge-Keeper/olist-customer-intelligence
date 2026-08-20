from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol
from uuid import uuid4

from olist_data_platform.platform.logging import LoggerFactory

from .datasets import MUNICIPALITY_POPULATION
from .municipality_population_extractor import MunicipalityPopulationExtractor
from .sidra_parser import SidraParser
from .sidra_query import SidraQuery

logger = LoggerFactory.get_logger(__name__)


class SidraValuesClient(Protocol):
    def get_values(self, query: SidraQuery) -> list[Any]: ...


class MunicipalityPopulationWriter(Protocol):
    def write(self, records: list[dict[str, Any]], request_id: str) -> None: ...


class MunicipalityPopulationIngestionService:
    def __init__(
        self,
        client: SidraValuesClient,
        bronze_writer: MunicipalityPopulationWriter,
        request_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.client = client
        self.bronze_writer = bronze_writer
        self.request_id_factory = request_id_factory or (lambda: str(uuid4()))

    def ingest(
        self,
        periods: tuple[str, ...] = ("2016", "2017", "2018"),
    ) -> str:
        request_id = self.request_id_factory()
        logger.info(
            "ibge_population_ingestion_started | request_id=%s | periods=%s",
            request_id,
            periods,
        )
        try:
            records: list[dict[str, Any]] = []
            for period in periods:
                logger.info(
                    "ibge_population_period_started | request_id=%s | period=%s",
                    request_id,
                    period,
                )
                query = MUNICIPALITY_POPULATION.build_query(
                    territories="all",
                    periods=(period,),
                )
                payload = self.client.get_values(query)
                decoded = SidraParser.decode(payload)
                period_records = MunicipalityPopulationExtractor.extract(decoded)
                if not period_records:
                    raise ValueError(
                        "IBGE population ingestion returned no records "
                        f"for period {period}."
                    )
                records.extend(period_records)
                logger.info(
                    "ibge_population_period_completed | "
                    "request_id=%s | period=%s | record_count=%s",
                    request_id,
                    period,
                    len(period_records),
                )

            if not records:
                raise ValueError("IBGE population ingestion returned no records.")

            self.bronze_writer.write(records, request_id)
            logger.info(
                "ibge_population_ingestion_completed | "
                "request_id=%s | record_count=%s",
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
