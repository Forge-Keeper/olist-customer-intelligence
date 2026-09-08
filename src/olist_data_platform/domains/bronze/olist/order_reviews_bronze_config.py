from olist_data_platform.platform.delta import (
    BRONZE_INGESTION_TIMESTAMP,
    ColumnContract,
    DatasetContract,
    TableMetadata,
)
from olist_data_platform.platform.delta.bronze import WriteStrategy

OLIST_ORDER_REVIEWS_BRONZE_CONFIG = DatasetContract(
    columns=(
        ColumnContract(
            name="review_id",
            data_type="string",
            nullable=False,
            description="Review identifier from the Olist source snapshot.",
        ),
        ColumnContract(
            name="order_id",
            data_type="string",
            nullable=False,
            description="Order identifier associated with the source review.",
        ),
        ColumnContract(
            name="review_score",
            data_type="string",
            nullable=False,
            description="Review score preserved exactly as source text.",
        ),
        ColumnContract(
            name="review_comment_title",
            data_type="string",
            nullable=True,
            description=(
                "Optional review title preserved exactly as source text, including "
                "source whitespace."
            ),
        ),
        ColumnContract(
            name="review_comment_message",
            data_type="string",
            nullable=True,
            description=(
                "Optional review message preserved exactly as source text, including "
                "embedded line breaks and source whitespace."
            ),
        ),
        ColumnContract(
            name="review_creation_date",
            data_type="string",
            nullable=False,
            description="Review creation date preserved exactly as source text.",
        ),
        ColumnContract(
            name="review_answer_timestamp",
            data_type="string",
            nullable=False,
            description="Review answer timestamp preserved exactly as source text.",
        ),
        ColumnContract(
            name="source_file",
            data_type="string",
            nullable=True,
            description="Source CSV file path captured from Spark file metadata.",
        ),
    ),
    managed_columns=(BRONZE_INGESTION_TIMESTAMP,),
    key_columns=("review_id", "order_id"),
    write_strategy=WriteStrategy.FULL_REPLACE,
    metadata=TableMetadata(
        description=(
            "Olist order reviews CSV snapshot landed in Bronze as source strings."
        ),
        tags={
            "layer": "bronze",
            "domain": "olist",
            "source_system": "olist_csv",
        },
    ),
)
