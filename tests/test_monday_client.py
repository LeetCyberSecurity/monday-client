import time
from unittest.mock import MagicMock, patch

import pytest
from pyrate_limiter import Duration, Rate, RateItem

from monday_client.monday import (BucketFullException, ComplexityLimitExceeded,
                                  MondayClient, MutationLimitExceeded)


# Fixture to create an instance of MondayClient with a test API key
@pytest.fixture
def monday_client():
    return MondayClient("test_api_key")

# Test to verify retry logic when complexity limit is exceeded and then succeeds
@patch('monday_client.monday.requests.post')  # Mock the requests.post method
@patch('monday_client.monday.time.sleep')  # Mock the time.sleep method
def test_complexity_limit_exceeded_retry_success(mock_sleep, mock_post, monday_client):
    # Mock response indicating complexity limit exceeded
    error_response = {
        'error_message': 'Complexity limit exceeded, reset in 10 seconds',
        'error_code': 'ComplexityException'
    }
    # Set up the mock to return the error response 3 times, then a success response
    mock_post.side_effect = [
        MagicMock(json=MagicMock(return_value=error_response))
        for _ in range(3)
    ] + [
        MagicMock(json=MagicMock(return_value={'data': 'success'}))
    ]

    # Call the method under test
    result = monday_client.post_request("test_query", "query")

    # Verify that the post request was made 4 times (3 retries + 1 success)
    assert mock_post.call_count == 4
    # Verify that sleep was called at least 3 times
    assert mock_sleep.call_count >= 3
    # Verify that sleep was called with 10 seconds each time
    ten_second_calls = [call for call in mock_sleep.call_args_list if call == call(10)]
    assert len(ten_second_calls) >= 3
    # Verify that the final result is a success response
    assert result == {'data': 'success'}

# Test to verify behavior when complexity limit is exceeded and max retries are reached
@patch('monday_client.monday.requests.post')  # Mock the requests.post method
@patch('monday_client.monday.time.sleep')  # Mock the time.sleep method
def test_complexity_limit_exceeded_max_retries(mock_sleep, mock_post, monday_client):
    # Mock response indicating complexity limit exceeded
    error_response = {
        'error_message': 'Complexity limit exceeded, reset in 10 seconds',
        'error_code': 'ComplexityException'
    }
    # Set up the mock to return the error response 4 times
    mock_post.side_effect = [
        MagicMock(json=MagicMock(return_value=error_response))
        for _ in range(4)
    ]

    # Call the method under test and expect an exception
    with pytest.raises(ComplexityLimitExceeded) as exc_info:
        monday_client.post_request("test_query", "query")

    # Verify that the post request was made 4 times
    assert mock_post.call_count == 4
    # Verify that sleep was called at least 3 times
    assert mock_sleep.call_count >= 3
    # Verify that sleep was called with 10 seconds each time
    ten_second_calls = [call for call in mock_sleep.call_args_list if call == call(10)]
    assert len(ten_second_calls) >= 3
    # Verify that the exception message is correct
    assert str(exc_info.value) == "Complexity limit exceeded, retrying after 10 seconds..."

# Test to verify successful request without any exceptions
@patch('monday_client.monday.requests.post')  # Mock the requests.post method
def test_successful_request(mock_post, monday_client):
    # Mock a successful response
    mock_post.return_value.json.return_value = {'data': 'success'}

    # Call the method under test
    result = monday_client.post_request("test_query", "query")

    # Verify that the result is a success response
    assert result == {'data': 'success'}
    # Verify that the post request was made only once
    assert mock_post.call_count == 1

# Test to verify behavior when mutation limit is exceeded and retries are performed
@patch('monday_client.monday.requests.post')  # Mock the requests.post method
@patch('monday_client.monday.time.sleep')  # Mock the time.sleep method
def test_mutation_limit_exceeded_with_retries(mock_sleep, mock_post, monday_client):
    # Mock response indicating mutation limit exceeded
    error_response = {
        'error_message': 'Mutation limit exceeded',
        'status_code': 429
    }
    # Set up the mock to return the error response 4 times (3 retries + 1 initial attempt)
    mock_post.side_effect = [
        MagicMock(json=MagicMock(return_value=error_response))
        for _ in range(4)
    ]

    # Call the method under test and expect an exception
    with pytest.raises(MutationLimitExceeded) as exc_info:
        monday_client.post_request("test_mutation", "mutation")

    # Verify that the post request was made 4 times
    assert mock_post.call_count == 4
    # Verify that sleep was called at least 3 times
    assert mock_sleep.call_count >= 3
    # Verify that sleep was called with 60 seconds each time
    sixty_second_calls = [call for call in mock_sleep.call_args_list if call == call(60)]
    assert len(sixty_second_calls) >= 3
    # Verify that the exception message is correct
    assert str(exc_info.value) == "Mutation per minute limit exceeded, retrying after 60 seconds..."

# Test to verify rate limiting logic
@patch('monday_client.monday.requests.post')  # Mock the requests.post method
@patch('monday_client.monday.time.sleep')  # Mock the time.sleep method
@patch('monday_client.monday.Limiter.try_acquire')  # Mock the Limiter.try_acquire method
def test_rate_limiting_logic(mock_try_acquire, mock_sleep, mock_post, monday_client):
    # Create mock RateItem and Rate instances
    rate_item_1 = RateItem('monday_client', time.time())
    rate_item_2 = RateItem('monday_client', time.time())
    rate = Rate(1, Duration.SECOND)

    # Create a mock exception instance
    bucket_full_exception_1 = BucketFullException(rate_item_1, rate)
    bucket_full_exception_1.meta_info = {'remaining_time': 2}
    bucket_full_exception_2 = BucketFullException(rate_item_2, rate)
    bucket_full_exception_2.meta_info = {'remaining_time': 2}

    # Simulate BucketFullException being raised twice before succeeding
    mock_try_acquire.side_effect = [
        bucket_full_exception_1,
        bucket_full_exception_2,
        None  # Succeed on the third attempt
    ]
    # Mock a successful response
    mock_post.return_value.json.return_value = {'data': 'success'}

    # Call the method under test
    result = monday_client.post_request("test_query", "query")

    # Verify that try_acquire was called three times
    assert mock_try_acquire.call_count == 3
    # Verify that sleep was called twice
    assert mock_sleep.call_count == 2
    # Verify that sleep was called with 2 seconds each time
    two_second_calls = [call for call in mock_sleep.call_args_list if call == call(2)]
    assert len(two_second_calls) == 2
    # Verify that the request was successful
    assert result == {'data': 'success'}
    # Verify that the post request was made once
    assert mock_post.call_count == 1