import time
from unittest.mock import MagicMock, patch

import pytest

from monday_client.monday import MondayClient


@pytest.fixture
def monday_client():
    return MondayClient(api_key="test_api_key", debug_logger=MagicMock(), info_logger=MagicMock())

def test_execute_post_request_rate_limit(monday_client):
    with patch('requests.post') as mock_post:  # Updated module path
        mock_post.return_value.json.return_value = {"data": {"complexity": {"before": 10000000, "after": 9999000, "reset_in_x_seconds": 60}}}
        for _ in range(5000):
            monday_client._execute_post_request("query { boards { id } }", "query")
        assert mock_post.call_count == 5000

def test_execute_post_request_retry_on_complexity_limit(monday_client):
    with patch('requests.post') as mock_post:  # Updated module path
        mock_post.return_value.json.side_effect = [
            {"data": {"complexity": {"before": 10000000, "after": 0, "reset_in_x_seconds": 1}}},
            {"data": {"complexity": {"before": 10000000, "after": 9999000, "reset_in_x_seconds": 60}}}
        ]
        with patch('time.sleep', return_value=None):
            monday_client._execute_post_request("query { boards { id } }", "query")
        assert mock_post.call_count == 2

def test_complexity_used_reset(monday_client):
    with patch('requests.post') as mock_post:  # Updated module path
        mock_post.return_value.json.return_value = {"data": {"complexity": {"before": 10000000, "after": 9999000, "reset_in_x_seconds": 60}}}
        monday_client._execute_post_request("query { boards { id } }", "query")
        assert monday_client._complexity_used == 1000
        mock_post.return_value.json.return_value = {"data": {"complexity": {"before": 10000000, "after": 10000000, "reset_in_x_seconds": 60}}}
        monday_client._execute_post_request("query { boards { id } }", "query")
        assert monday_client._complexity_used == 0

def test_execute_post_request_mutation_limit(monday_client):
    with patch('requests.post') as mock_post:  # Updated module path
        mock_post.return_value.json.return_value = {"data": {"complexity": {"before": 10000000, "after": 9999000, "reset_in_x_seconds": 60}}}
        with patch('time.sleep', return_value=None):
            for _ in range(2000):
                monday_client._execute_post_request("mutation { create_item }", "mutation")
        assert mock_post.call_count == 2000

def test_execute_post_request_special_mutation_limit(monday_client):
    with patch('requests.post') as mock_post:  # Updated module path
        mock_post.return_value.json.return_value = {"data": {"complexity": {"before": 10000000, "after": 9999000, "reset_in_x_seconds": 60}}}
        with patch('time.sleep', return_value=None):
            for _ in range(40):
                monday_client._execute_post_request("mutation { duplicate_board }", "mutation")
        assert mock_post.call_count == 40