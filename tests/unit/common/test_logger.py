import logging

import pytest

from olist_data_platform.platform.logging.logger import LoggerFactory


def test_should_return_logger_instance():
    logger = LoggerFactory.get_logger("test_logger_instance")
    assert isinstance(logger, logging.Logger)


def test_should_use_provided_logger_name():
    logger = LoggerFactory.get_logger("test_custom_name")
    assert logger.name == "test_custom_name"


def test_should_use_default_log_level():
    logger = LoggerFactory.get_logger("test_default_level")
    assert logger.level == logging.INFO


def test_should_use_custom_log_level():
    logger = LoggerFactory.get_logger(
        "test_custom_level",
        level=logging.DEBUG,
    )
    assert logger.level == logging.DEBUG


def test_should_create_stream_handler():
    logger = LoggerFactory.get_logger("test_stream_handler")
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_should_not_duplicate_handlers():
    logger_name = "test_duplicate_handlers"

    first_logger = LoggerFactory.get_logger(logger_name)
    second_logger = LoggerFactory.get_logger(logger_name)

    assert first_logger is second_logger
    assert len(first_logger.handlers) == 1


def test_should_configure_expected_formatter():
    logger = LoggerFactory.get_logger("test_formatter")

    handler = logger.handlers[0]
    formatter = handler.formatter

    assert formatter is not None
    assert formatter._fmt == LoggerFactory.DEFAULT_FORMAT


def test_should_configure_expected_date_format():
    logger = LoggerFactory.get_logger("test_date_formatter")

    handler = logger.handlers[0]
    formatter = handler.formatter

    assert formatter is not None
    assert formatter.datefmt == LoggerFactory.DATE_FORMAT


def test_should_disable_log_propagation():
    logger = LoggerFactory.get_logger("test_propagation")
    assert logger.propagate is False


@pytest.mark.parametrize("name", ["", " "])
def test_should_reject_empty_logger_name(name):
    with pytest.raises(
        ValueError,
        match="Logger name cannot be empty",
    ):
        LoggerFactory.get_logger(name)


@pytest.mark.parametrize(
    "name",
    [
        None,
        123,
        [],
        {},
    ],
)
def test_should_reject_non_string_logger_name(name):
    with pytest.raises(
        TypeError,
        match="Logger name must be a string",
    ):
        LoggerFactory.get_logger(name)
