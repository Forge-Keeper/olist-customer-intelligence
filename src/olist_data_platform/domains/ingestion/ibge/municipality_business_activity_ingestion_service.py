from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol
from uuid import uuid4

from olist_data_platform.platform.logging import LoggerFactory

from .datasets import MUNICIPALITY_BUSINESS_ACTIVITY
from .municipality_business_activity_extractor import (
    MunicipalityBusinessActivityExtractor,
)
from .sidra_parser import SidraParser
from .sidra_query import SidraQuery

logger = LoggerFactory.get_logger(__name__)


class SidraValuesClient(Protocol):
    def get_values(self, query: SidraQuery) -> list[Any]: ...


class MunicipalityBusinessActivityWriter(Protocol):
    def write(self, records: list[dict[str, Any]], request_id: str) -> None: ...


class MunicipalityBusinessActivityIngestionService:
    def __init__(
        self,
        client: SidraValuesClient,
        bronze_writer: MunicipalityBusinessActivityWriter,
        request_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self.client = client
        self.bronze_writer = bronze_writer
        self.request_id_factory = request_id_factory or (lambda: str(uuid4()))

    def ingest(
        self,
        periods: tuple[str, ...] = MUNICIPALITY_BUSINESS_ACTIVITY.default_periods,
    ) -> str:
        request_id = self.request_id_factory()
        logger.info(
            "ibge_cempre_ingestion_started | request_id=%s | periods=%s | variables=%s",
            request_id,
            periods,
            MUNICIPALITY_BUSINESS_ACTIVITY.variables,
        )
        try:
            records: list[dict[str, Any]] = []
            for period in periods:
                for variable_code in MUNICIPALITY_BUSINESS_ACTIVITY.variables:
                    query = MUNICIPALITY_BUSINESS_ACTIVITY.build_query(
                        territories="all",
                        periods=(period,),
                        variables=(variable_code,),
                    )
                    payload = self.client.get_values(query)
                    decoded = SidraParser.decode(payload)
                    slice_records = MunicipalityBusinessActivityExtractor.extract(decoded)
                    if not slice_records:
                        raise ValueError(
                            "IBGE CEMPRE ingestion returned no records "
                            f"for period {period} and variable {variable_code}."
                        )
                    records.extend(slice_records)
                    logger.info(
                        "ibge_cempre_slice_completed | request_id=%s | period=%s | "
                        "variable=%s | record_count=%s",
                        request_id,
                        period,
                        variable_code,
                        len(slice_records),
                    )

            if not records:
                raise ValueError("IBGE CEMPRE ingestion returned no records.")

            self.bronze_writer.write(records, request_id)
            logger.info(
                "ibge_cempre_ingestion_completed | request_id=%s | record_count=%s",
                request_id,
                len(records),
            )
            return request_id
        except Exception:
            logger.exception(
                "ibge_cempre_ingestion_failed | request_id=%s | periods=%s",
                request_id,
                periods,
            )
            raise
