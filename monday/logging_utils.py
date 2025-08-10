"""
Logging utilities for the Monday client.

This module provides convenient utilities to configure logging for the Monday client library.
The Monday client follows Python library best practices by using a NullHandler by default,
allowing applications to control logging behavior.

Quick usage:
    >>> from monday import enable_logging
    >>> enable_logging()  # Enable with defaults

Advanced usage:
    >>> from monday import configure_for_external_logging
    >>> configure_for_external_logging()
    >>> # Then configure 'monday' logger in your logging config
"""

import logging
import sys


def enable_logging(
    level: int | str = logging.INFO,
    format_string: str | None = None,
    handler: logging.Handler | None = None,
) -> None:
    """
    Enable logging for the Monday client with a dedicated handler.

    This function removes any existing NullHandlers and adds a StreamHandler (or custom handler)
    to the Monday logger. It also ensures propagation is enabled, making it safe to call after
    disable_logging().

    Args:
        level: Log level (e.g., logging.DEBUG, logging.INFO, 'DEBUG', 'INFO')
        format_string: Custom format string for log messages. Defaults to '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        handler: Custom handler to use. Defaults to StreamHandler(sys.stdout)

    Note:
        - Calling this multiple times won't create duplicate handlers
        - Always sets propagate=True, overriding any previous disable_logging() call
        - If you prefer external logging configuration, use configure_for_external_logging() instead

    Example:
        >>> from monday import enable_logging
        >>> enable_logging(level='DEBUG')
        >>> # or with specific format
        >>> enable_logging(level='INFO', format_string='%(name)s: %(message)s')

    """
    logger = logging.getLogger('monday')

    # Remove any existing NullHandlers
    for existing_handler in logger.handlers[:]:
        if isinstance(existing_handler, logging.NullHandler):
            logger.removeHandler(existing_handler)

    # Don't add a new handler if one already exists (unless it's a NullHandler)
    if not logger.handlers:
        if handler is None:
            handler = logging.StreamHandler(sys.stdout)

        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        formatter = logging.Formatter(format_string)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Set the log level
    if isinstance(level, str):
        level = getattr(logging, level.upper())
    logger.setLevel(level)

    # Ensure propagation is enabled (might have been disabled by disable_logging)
    logger.propagate = True


def disable_logging() -> None:
    """
    Completely disable logging for the Monday client.

    This function removes all existing handlers, adds a NullHandler, and sets propagate=False
    to ensure no Monday client logs appear anywhere, even if the root logger is configured.

    Note:
        - This completely silences Monday client logs, regardless of your app's logging setup
        - To re-enable logging, call enable_logging() which will restore normal behavior
        - More aggressive than just setting a high log level

    Example:
        >>> from monday import disable_logging
        >>> disable_logging()
        >>> # Monday client will produce no log output

    """
    logger = logging.getLogger('monday')

    # Remove all existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    # Add NullHandler to suppress all logging
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.NOTSET)
    logger.propagate = False


def set_log_level(level: int | str) -> None:
    """
    Set the log level for the Monday client logger.

    This only changes the level - it doesn't add or remove handlers. Use enable_logging()
    or configure_for_external_logging() first to ensure the logger has appropriate handlers.

    Args:
        level: Log level (e.g., logging.DEBUG, logging.INFO, 'DEBUG', 'INFO')

    Note:
        - If the Monday logger only has a NullHandler, changing the level won't make logs appear
        - Use this to fine-tune logging verbosity after setting up handlers

    Example:
        >>> from monday import enable_logging, set_log_level
        >>> enable_logging()  # Set up handlers first
        >>> set_log_level('DEBUG')  # Now change level
        >>> set_log_level('WARNING')  # Reduce verbosity

    """
    logger = logging.getLogger('monday')

    if isinstance(level, str):
        level = getattr(logging, level.upper())

    logger.setLevel(level)


def get_logger() -> logging.Logger:
    """
    Get the Monday client logger instance.

    This returns the same logger instance used internally by the Monday client.
    Useful for advanced logging configuration or adding custom handlers.

    Returns:
        The Monday client logger (equivalent to logging.getLogger('monday'))

    Note:
        - This is the same logger that enable_logging() and disable_logging() modify
        - You can use this for direct logger manipulation if the utility functions don't meet your needs
        - Changes to this logger affect all Monday client logging

    Example:
        >>> from monday import get_logger
        >>> logger = get_logger()
        >>> logger.addHandler(your_custom_handler)
        >>> logger.info('Custom log message')

    """
    return logging.getLogger('monday')


def is_logging_enabled() -> bool:
    """
    Check if logging is currently enabled for the Monday client.

    This checks whether the Monday logger has any handlers other than NullHandler.
    Note that even with only a NullHandler, logs may still appear if propagate=True
    and a parent logger (like root) has handlers configured.

    Returns:
        True if the Monday logger has non-NullHandler handlers, False otherwise

    Note:
        - Returns False if only NullHandler is present, even if logs might still appear via propagation
        - Use this to check if enable_logging() has been called successfully
        - Does not account for external logging configuration via configure_for_external_logging()

    Example:
        >>> from monday import is_logging_enabled, enable_logging
        >>> print(is_logging_enabled())  # False initially
        >>> enable_logging()
        >>> print(is_logging_enabled())  # True after enabling

    """
    logger = logging.getLogger('monday')

    # Check if there are any handlers other than NullHandler
    for handler in logger.handlers:
        if not isinstance(handler, logging.NullHandler):
            return True

    return False


def configure_for_external_logging() -> None:
    """
    Prepare the Monday client logger for external logging configuration.

    This removes the default NullHandler and sets the logger level to NOTSET,
    allowing the logger to inherit configuration from parent loggers or be
    configured via logging.config.dictConfig().

    Use this when you want to manage Monday client logging through your
    application's centralized logging configuration instead of enable_logging().

    Note:
        - After calling this, Monday logs will appear if your app configures logging (via basicConfig, dictConfig, etc.)
        - Sets level to NOTSET for proper inheritance
        - Keeps propagate=True to allow inheritance from parent loggers
        - Required when using dictConfig() with explicit Monday logger configuration

    Example:
        >>> from monday import configure_for_external_logging
        >>> import logging
        >>> configure_for_external_logging()
        >>> logging.basicConfig(level=logging.INFO)  # Monday logs will now appear
        >>> # Or with dictConfig:
        >>> configure_for_external_logging()
        >>> logging.config.dictConfig(
        ...     your_config
        ... )  # Configure Monday logger in your_config

    """
    logger = logging.getLogger('monday')

    # Remove the default NullHandler
    for handler in logger.handlers[:]:
        if isinstance(handler, logging.NullHandler):
            logger.removeHandler(handler)

    # Don't add any handlers - let external config handle it
    # Set level to NOTSET so it inherits from parent loggers
    logger.setLevel(logging.NOTSET)
