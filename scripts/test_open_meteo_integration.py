from datetime import date
from pprint import pprint

from olist_data_platform.ingestion.api.open_meteo_client import (
    OpenMeteoClient,
)


def main() -> None:
    client = OpenMeteoClient(
        timeout=30,
        max_retries=2,
        backoff_factor=1.0,
    )

    response = client.get_historical_weather(
        latitude=-23.5505,
        longitude=-46.6333,
        start_date=date(2018, 1, 1),
        end_date=date(2018, 1, 3),
        timezone="America/Sao_Paulo",
    )

    pprint(response)


if __name__ == "__main__":
    main()