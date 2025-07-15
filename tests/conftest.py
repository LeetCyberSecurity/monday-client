"""Pytest configuration for monday-client tests."""

import logging
import os
from pathlib import Path

import pytest
import yaml


def load_config_from_file(config_path: str | None = None) -> dict:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to config file. If None, looks for config.yml in tests/integrations.

    Returns:
        Dictionary containing configuration values.

    """
    if config_path is None:
        # Look for config.yml in tests/integrations directory
        config_file_path = Path(__file__).parent / 'integrations' / 'config.yml'
    else:
        config_file_path = Path(config_path)

    if not config_file_path.exists():
        return {}

    try:
        with config_file_path.open(encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (yaml.YAMLError, OSError) as e:
        logging.getLogger(__name__).warning(
            'Could not load config file %s: %s', config_file_path, e
        )
        return {}


def get_config_value(
    key: str, default: str | None = None, config: dict | None = None
) -> str | int | float | bool | list | dict | None:
    """
    Get a configuration value from config dict or environment variable.

    Config dict values take precedence over environment variables.

    Args:
        key: Configuration key (e.g., 'monday.api_key')
        default: Default value if not found
        config: Configuration dictionary

    Returns:
        Configuration value or default

    """
    if config:
        # Navigate nested keys (e.g., 'monday.api_key' -> config_dict['monday']['api_key'])
        keys = key.split('.')
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                value = None
                break

        if value is not None:
            return value

    # Fall back to environment variable
    env_key = key.upper().replace('.', '_')
    return os.getenv(env_key, default)


def get_monday_config(config: dict | None = None) -> dict:
    """
    Get monday.com specific configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Dictionary with monday.com configuration

    """
    return {
        'api_key': get_config_value('monday.api_key', config=config),
        'board_id': get_config_value('monday.board_id', config=config),
        'item_id': get_config_value('monday.item_id', config=config),
        'user_id': get_config_value('monday.user_id', config=config),
        'subitem_id': get_config_value('monday.subitem_id', config=config),
        'user_email': get_config_value('monday.user_email', config=config),
        'group_id': get_config_value('monday.group_id', config=config),
        'workspace_id': get_config_value('monday.workspace_id', config=config),
        'column_id': get_config_value('monday.column_id', config=config),
        'column_values': get_config_value('monday.column_values', config=config),
    }


def pytest_configure(config: pytest.Config) -> None:
    """Configure logging based on command line options."""
    # Check if logging is requested
    log_level: str | None = config.getoption('--logging', default=None)

    if log_level:
        # Configure pytest logging to show monday logs
        config.option.log_cli = True
        config.option.log_cli_level = log_level.upper()
        config.option.log_cli_format = (
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Enable logging for monday modules at the specified level
        logging.getLogger('monday').setLevel(getattr(logging, log_level.upper()))


def pytest_runtest_setup(
    item: pytest.Item,  # noqa: ARG001
) -> None:
    """Remove NullHandler after modules are imported."""
    # Always remove the NullHandler that monday-client adds and add a real handler
    monday_logger = logging.getLogger('monday')

    for handler in monday_logger.handlers[:]:
        if isinstance(handler, logging.NullHandler):
            monday_logger.removeHandler(handler)

    # Add a real handler to monday logger if it doesn't have one
    if not monday_logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        monday_logger.addHandler(handler)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command line options."""
    parser.addoption(
        '--logging',
        type=str,
        choices=['debug', 'info', 'warning', 'error', 'critical'],
        help='Enable logging for monday modules at specified level (debug, info, warning, error, critical)',
    )
    parser.addoption(
        '--config',
        type=str,
        help='Path to configuration file (defaults to tests/integrations/config.yml)',
    )


@pytest.fixture(scope='session')
def get_config(request: pytest.FixtureRequest) -> dict:
    """Load configuration for the test session."""
    config_path = request.config.getoption('--config')
    return load_config_from_file(config_path)


@pytest.fixture(scope='session')
def monday_config(
    get_config: dict,
) -> dict:
    """Get monday.com specific configuration."""
    return get_monday_config(get_config)
