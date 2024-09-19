import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Union

import requests
from pyrate_limiter import BucketFullException, Duration, Limiter, Rate
from tenacity import retry, retry_if_exception_type, stop_after_attempt

from .exceptions import ComplexityLimitExceeded, MutationLimitExceeded
from .services.boards import Boards
from .services.items import Items


class MondayClient:
	"""
	Client for interacting with the Monday.com API.
	This client handles API requests, rate limiting, and pagination for Monday.com's GraphQL API.

	It uses a class-level logger named 'monday_client' for all logging operations.

	Attributes:
		url (str): The endpoint URL for the Monday.com API.
		headers (dict): HTTP headers used for API requests, including authentication.

	Args:
		api_key (str): The API key for authenticating with the Monday.com API.

	Note:
		Logging can be controlled by configuring the 'monday_client' logger.
		By default, a NullHandler is added to the logger, which suppresses all output.
		To enable logging, configure the logger in your application code. For example:

		```python
		import logging
		logger = logging.getLogger('monday_client')
		logger.setLevel(logging.INFO)
		handler = logging.StreamHandler()
		handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
		logger.addHandler(handler)
		```

		To disable all logging (including warnings and errors):

		```python
		import logging
		logging.getLogger('monday_client').disabled = True
		```

	Example:
		```python
		from monday_client import MondayClient
		client = MondayClient(api_key='your_api_key')
		```
	"""

	logger = logging.getLogger(__name__)

	def __init__(self, api_key: str, url: str = 'https://api.monday.com/v2', headers: Optional[Dict[str, Any]] = None):
		"""
		Initialize the MondayClient with the provided API key.

		Args:
			api_key (str): The API key for authenticating with the Monday.com API.
			url (str, optional): The endpoint URL for the Monday.com API. Defaults to 'https://api.monday.com/v2'.
			headers (dict, optional): Additional HTTP headers used for API requests. Defaults to None.
		"""
		self.url = url
		self.headers = {'Content-Type': 'application/json', 'Authorization': f'{api_key}', **(headers or {})}
		self.rate_limit = Rate(5000, Duration.MINUTE)
		self.limiter = Limiter(self.rate_limit)
		self.boards = Boards(self)
		self.items = Items(self)

	def post_request(self, query: str) -> Union[Dict[str, Any], bool]:
		"""
		Executes a single post request to the Monday.com API.

		Args:
			query (str): The GraphQL query string to be executed.

		Returns:
			Dict[str, Any]: The response data from the API
		"""
		return self._execute_post_request(query)

	@staticmethod
	def _sleep_before_retry(retry_state):
		"""
		Sleeps for the required amount of time before retrying a request.

		Args:
			retry_state: The state of the retry attempt.
		"""
		if retry_state.outcome.failed:
			exception = retry_state.outcome.exception()
			if isinstance(exception, ComplexityLimitExceeded):
				sleep_time = int(exception.reset_in)
				time.sleep(sleep_time)
			elif isinstance(exception, MutationLimitExceeded):
				time.sleep(60)

	@retry(
		stop=stop_after_attempt(4),
		retry=retry_if_exception_type((ComplexityLimitExceeded, MutationLimitExceeded)),
		before_sleep=_sleep_before_retry,
		reraise=True
	)
	def _execute_post_request(self, query: str) -> Dict[str, Any]:
		"""
		Executes a post request to the Monday.com API with rate limiting and retry logic.

		Args:
			query (str): The GraphQL query string to be executed.

		Returns:
			Dict[str, Any]: The response data from the API.
		"""
		while True:
			try:
				# Attempt to acquire a token for 'monday_client'
				self.limiter.try_acquire('monday_client')
				break  # Exit the loop if token is acquired successfully
			except BucketFullException as e:
				# If rate limit is exceeded, log and sleep for the remaining time
				rate_limit_sleep_time = e.meta_info['remaining_time']
				self.logger.info(f'Rate limit exceeded. Sleeping for {rate_limit_sleep_time} seconds.')
				time.sleep(rate_limit_sleep_time)

		self.logger.info(f'submitting query: {query}')
		response = requests.post(self.url, json={'query': query}, headers=self.headers)
		response_data = response.json()
		self.logger.debug(f'response to {query}: {response_data}')

		if any('error' in key for key in response_data.keys()):
			if 'error_code' in response_data and response_data['error_code'] == 'ComplexityException':
				reset_in_search = re.search(r'reset in (\d+) seconds', response_data['error_message'])
				if reset_in_search:
					reset_in = int(reset_in_search.group(1))
				else:
					self.logger.error(f'error getting reset_in_x_seconds: {response_data}')
					return {'error': response_data}
				raise ComplexityLimitExceeded(f'Complexity limit exceeded, retrying after {reset_in} seconds...', reset_in)
			if 'status_code' in response_data and int(response_data['status_code']) == 429:
				raise MutationLimitExceeded(f'Mutation per minute limit exceeded, retrying after 60 seconds...')
			return {'error': response_data}
		
		return response_data
	
logging.getLogger('monday_client').addHandler(logging.NullHandler())