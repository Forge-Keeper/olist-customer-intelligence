from pathlib import Path

from olist_data_platform.domains.ingestion.olist.csv_snapshot_reader import (
    OlistCsvSnapshotReader,
)


def test_order_reviews_reader_preserves_multiline_comment(spark, tmp_path):
    source = Path(tmp_path) / "olist_order_reviews_dataset.csv"
    source.write_text(
        "review_id,order_id,review_score,review_comment_title,review_comment_message,review_creation_date,review_answer_timestamp\n"
        'review-1,order-1,5,title,"first line\nsecond line",2018-01-01 00:00:00,2018-01-02 10:30:00\n',
        encoding="utf-8",
    )

    reader = OlistCsvSnapshotReader(
        spark=spark,
        source_path=str(source),
        required_columns=(
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ),
        dataset_name="olist_order_reviews",
        multiline=True,
        escape='"',
    )

    rows = reader.read().collect()

    assert len(rows) == 1
    assert rows[0]["review_comment_message"] == "first line\nsecond line"
    assert rows[0]["source_file"]
