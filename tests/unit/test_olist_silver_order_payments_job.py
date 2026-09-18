from argparse import Namespace
from types import SimpleNamespace
from unittest.mock import MagicMock

import olist_data_platform.jobs.olist_silver_order_payments as job_module


def _args() -> Namespace:
    return Namespace(
        source_table="dev.bronze.olist_order_payments",
        orders_table="dev.silver.olist_orders",
        target_table="dev.silver.olist_order_payments",
        execution_runs_table="dev_admin.operations.execution_runs",
        quality_results_table="dev_admin.quality.data_quality_results",
    )


def test_parser_requires_source_orders_target_and_control_tables() -> None:
    args = job_module.build_parser().parse_args(
        [
            "--source-table",
            "dev.bronze.olist_order_payments",
            "--orders-table",
            "dev.silver.olist_orders",
            "--target-table",
            "dev.silver.olist_order_payments",
            "--execution-runs-table",
            "dev_admin.operations.execution_runs",
            "--quality-results-table",
            "dev_admin.quality.data_quality_results",
        ]
    )

    assert args == _args()


def test_run_tracks_execution_and_reads_explicit_inputs(monkeypatch) -> None:
    spark = MagicMock()
    bronze = MagicMock()
    orders = MagicMock()
    spark.table.side_effect = [bronze, orders]

    tracker = MagicMock()
    monkeypatch.setattr(
        job_module,
        "ExecutionRunRepository",
        lambda spark_session, target: ("repo", spark_session, target),
    )
    monkeypatch.setattr(
        job_module,
        "ExecutionRunTracker",
        lambda repository: tracker,
    )

    captured = {}

    def _process(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(row_count=3)

    monkeypatch.setattr(job_module, "process_order_payments_snapshot", _process)

    run_id, row_count = job_module.run(_args(), spark)

    assert row_count == 3
    assert run_id
    assert spark.table.call_args_list[0].args == (
        "dev.bronze.olist_order_payments",
    )
    assert spark.table.call_args_list[1].args == ("dev.silver.olist_orders",)
    assert captured["bronze"] is bronze
    assert captured["orders"] is orders
    assert captured["target_table"] == "dev.silver.olist_order_payments"
    assert captured["quality_results_table"] == (
        "dev_admin.quality.data_quality_results"
    )
    assert captured["run_id"] == run_id
    assert '"orders_table":"dev.silver.olist_orders"' in captured[
        "evaluation_scope"
    ]
    assert '"source_table":"dev.bronze.olist_order_payments"' in captured[
        "evaluation_scope"
    ]

    tracker.start.assert_called_once_with(
        run_id=run_id,
        dataset="olist_order_payments",
        layer="silver",
        source_system="olist_bronze",
        target_table="dev.silver.olist_order_payments",
        execution_scope=captured["evaluation_scope"],
    )
    tracker.succeed.assert_called_once_with(run_id)
    tracker.fail.assert_not_called()


def test_run_marks_tracker_failed_when_processor_raises(monkeypatch) -> None:
    spark = MagicMock()
    spark.table.side_effect = [MagicMock(), MagicMock()]

    tracker = MagicMock()
    monkeypatch.setattr(
        job_module,
        "ExecutionRunRepository",
        lambda spark_session, target: ("repo", spark_session, target),
    )
    monkeypatch.setattr(
        job_module,
        "ExecutionRunTracker",
        lambda repository: tracker,
    )

    failure = RuntimeError("boom")

    def _process(**kwargs):
        raise failure

    monkeypatch.setattr(job_module, "process_order_payments_snapshot", _process)

    try:
        job_module.run(_args(), spark)
    except RuntimeError as exc:
        assert exc is failure
    else:
        raise AssertionError("Expected processor failure to propagate.")

    tracker.fail.assert_called_once()
    assert tracker.fail.call_args.args[1] is failure
    tracker.succeed.assert_not_called()
