from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol
from uuid import uuid4

from olist_data_platform.platform.logging import LoggerFactory

from .datasets import MUNICIPALITY_GDP
from .municipality_gdp_extractor import MunicipalityGdpExtractor
from .sidra_parser import SidraParser
from .sidra_query import SidraQuery

logger = LoggerFactory.get_logger(__name__)


class SidraValuesClient(Protocol):
    def get_values(self, query: SidraQuery) -> list[Any]: ...


class MunicipalityGdpWriter(Protocol):
    def write(self, records: list[dict[str, Any]], request_id: str) -> None: ...


class MunicipalityGdpIngestionService:
    def __init__(
        self,
        client: SidraValuesClient,
        bronze_writer: MunicipalityGdpWriter,
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
            "ibge_gdp_ingestion_started | request_id=%s | periods=%s | variables=%s",
            request_id,
            periods,
            MUNICIPALITY_GDP.variables,
        )
        try:
            records: list[dict[str, Any]] = []
            for period in periods:
                for variable_code in MUNICIPALITY_GDP.variables:
                    logger.info(
                        "ibge_gdp_slice_started | request_id=%s | period=%s | variable=%s",
                        request_id,
                        period,
                        variable_code,
                    )
                    query = MUNICIPALITY_GDP.build_query(
                        territories="all",
                        periods=(period,),
                        variables=(variable_code,),
                    )
                    payload = self.client.get_values(query)
                    decoded = SidraParser.decode(payload)
                    slice_records = MunicipalityGdpExtractor.extract(decoded)
                    if not slice_records:
                        raise ValueError(
                            "IBGE municipal GDP ingestion returned no records "
                            f"for period {period} and variable {variable_code}."
                        )
                    records.extend(slice_records)
                    logger.info(
                        "ibge_gdp_slice_completed | request_id=%s | period=%s | "
                        "variable=%s | record_count=%s",
                        request_id,
                        period,
                        variable_code,
                        len(slice_records),
                    )

            if not records:
                raise ValueError("IBGE municipal GDP ingestion returned no records.")

            self.bronze_writer.write(records, request_id)
            logger.info(
                "ibge_gdp_ingestion_completed | request_id=%s | record_count=%s",
                request_id,
                len(records),
            )
            return request_id
        except Exception:
            logger.exception(
                "ibge_gdp_ingestion_failed | request_id=%s | periods=%s",
                request_id,
                periods,
            )
            raise
