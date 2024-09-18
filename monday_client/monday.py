import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Union

import requests
from pyrate_limiter import BucketFullException, Duration, Limiter, Rate
from tenacity import retry, retry_if_exception_type, stop_after_attempt


class ComplexityLimitExceeded(Exception):
	"""
	Exception raised when the complexity limit is exceeded.

	Attributes:
		message (str): Explanation of the error.
		reset_in (int): Time in seconds until the complexity limit is reset.
	"""
	def __init__(self, message: str, reset_in: int):
		super().__init__(message)
		self.reset_in = reset_in

class MutationLimitExceeded(Exception):
	"""
	Exception raised when the mutation per minute limit is exceeded.

	Attributes:
		message (str): Explanation of the error.
	"""
	def __init__(self, message: str):
		super().__init__(message)

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
		logging.getLogger('monday_client').setLevel(logging.CRITICAL)
		```

	Example:
		client = MondayClient(api_key='your_api_key')
	"""

	logger = logging.getLogger('monday_client')

	def __init__(self, api_key: str, url: str = 'https://api.monday.com/v2', headers: Optional[Dict[str, Any]] = None):
		"""
		Initialize the MondayClient with the provided API key.

		Args:
			api_key (str): The API key for authenticating with the Monday.com API.
			url (str, optional): The endpoint URL for the Monday.com API. Defaults to 'https://api.monday.com/v2'.
			headers (dict, optional): HTTP headers used for API requests. Defaults to None.
		"""
		self.url = url
		self.headers = {'Content-Type': 'application/json', 'Authorization': f'{api_key}', **(headers or {})}
		self.valid_query_types = ['query', 'mutation']
		self.rate_limit = Rate(5000, Duration.MINUTE)
		self.limiter = Limiter(self.rate_limit)

	def items_page(self, board_id: int, query_params: str = '', limit: int = 25, fields: str = 'id name column_values { id text value column { title } }') -> Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]:
		"""
		Retrieves a paginated list of items from a specified board on Monday.com.

		Args:
			board_id (int): The ID of the board from which to retrieve items.
			query_params (str, optional): Additional query parameters to filter the items. Defaults to ''.
			limit (int, optional): The maximum number of items to retrieve per page. Defaults to 25.
			fields (str, optional): The fields to include in the response. Defaults to 'id name column_values { id text value column { title } }'.

		Returns:
			Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]: A dictionary containing the combined items retrieved
			and a completion status. 
			The dictionary has the following structure:
				
				- 'items': A list of dictionaries representing the items retrieved.
				- 'completed': A boolean indicating whether the pagination was completed successfully.
		"""
		query = f'boards (ids: {board_id}) {{ items_page (limit: {limit}{", query_params: " + query_params if query_params else ""}) {{ cursor items {{ {fields} }} }} }}'
		return self.paginated_item_request(query, 'query', limit=limit)

	def paginated_item_request(self, query: str, query_type: str, limit: int = 25) -> Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]:
		"""
		Executes a paginated request to retrieve items from Monday.com.

		This method handles the pagination logic to retrieve all items from a board
		by repeatedly querying the API until all items are fetched.

		Args:
			query (str): The GraphQL query string to be executed.
			query_type (str): The type of the query, either 'query' or 'mutation'.
			limit (int, optional): The maximum number of items to retrieve per page. Defaults to 25.

		Returns:
			Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]: A dictionary containing the combined items retrieved,
			a completion status, and optionally the query string if an error occurs. The dictionary has the following structure:
				
				- 'items': A list of dictionaries representing the items retrieved.
				- 'completed': A boolean indicating whether the pagination was completed successfully.
				- 'query' (optional): The query string if an error occurs.
		"""
		combined_items = []
		cursor = 'start'

		while True:
			if cursor == 'start':
				paginated_query = query
			else:
				items_value = self._extract_items_query(query)
				if not items_value:
					return {'items': combined_items, 'completed': False}
				paginated_query = f'next_items_page (limit: {limit}, cursor: "{cursor}") {{ cursor {items_value} }}'

			self.logger.info(f'submitting paginated query: {paginated_query}')
			
			response_data = self._execute_post_request(paginated_query, query_type)
			if not response_data:
				return {'items': combined_items, 'completed': False}
			if 'error' in response_data:
				return {'errors': [response_data['error']], 'query': paginated_query, 'completed': False}
			
			items = self._extract_items(json.dumps(response_data))
			combined_items.extend(items)

			cursor = self._extract_cursor_value(json.dumps(response_data))
			if not cursor:
				break

		return {'items': combined_items, 'completed': True} 

	def post_request(self, query: str, query_type: str) -> Union[Dict[str, Any], bool]:
		"""
		Executes a single post request to the Monday.com API.

		Args:
			query (str): The GraphQL query string to be executed.
			query_type (str): The type of the query, either 'query' or 'mutation'.

		Returns:
			Union[Dict[str, Any], bool]: The response data from the API, or False if the request failed.
		"""
		return self._execute_post_request(query, query_type) or False

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
	def _execute_post_request(self, query: str, query_type: str) -> Union[Dict[str, Any], bool]:
		"""
		Executes a post request to the Monday.com API with rate limiting and retry logic.

		Args:
			query (str): The GraphQL query string to be executed.
			query_type (str): The type of the query, either 'query' or 'mutation'.

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

		query_type = query_type.lower()
		if query_type not in self.valid_query_types:
			self.logger.error(f'invalid query type: {query_type}')
			return {'error': 'Invalid query type'}

		query = f'{query_type} {{ {query} }}'
		self.logger.info(f'submitting query: {query}')
		response = requests.post(self.url, json={'query': query}, headers=self.headers)
		response_data = response.json()
		self.logger.debug(f'response to query {query}: {response_data}')

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
			error_message = response_data['errors'][0]['message']
			self.logger.error(f'GraphQL error: {error_message}')
			return {'error': error_message}
		
		return response_data or False
		
	def _extract_cursor_value(self, response_data: str) -> Optional[str]:
		"""
		Extracts the cursor value from the response data.

		Args:
			response_data (str): The JSON response data as a string.

		Returns:
			Optional[str]: The cursor value if it can be extracted, otherwise None.
		"""
		cursor_pattern = re.compile(r'"cursor":\s*(?:"([^"]+)"|null)')
		match = cursor_pattern.search(response_data)
		if match:
			cursor_value = match.group(1)
			return cursor_value
		else:
			self.logger.warning(f'Could not extract cursor value from response data: {response_data}')
			return None
		
	def _extract_items_query(self, query: str) -> Optional[str]:
		"""
		Extracts the items query from a GraphQL query string.

		Args:
			query (str): The GraphQL query string.

		Returns:
			Optional[str]: The items query string if it can be extracted, otherwise None.
		"""
		items_query_pattern = re.compile(r'items\s*{[^{}]*(?:{[^}]*}[^{}]*)*}')
		match = items_query_pattern.search(query)
		if match:
			items_value = match.group(0)
			items_value = re.sub(r'\s*cursor\s*(?=})', '', items_value)
			return items_value
		else:
			self.logger.warning(f'Could not extract items value from query: {query}')
			return None
		
	def _extract_items(self, response_data: str) -> List[Dict[str, Any]]:
		"""
		Extracts the items from the response data.

		Args:
			response_data (str): The JSON response data as a string.

		Returns:
			List[Dict[str, Any]]: A list of dictionaries representing the items.
		"""
		items_pattern = re.compile(r'"items"\s*:\s*(\[(?:[^[\]]*|\[(?:[^[\]]*|\[[^[\]]*\])*\])*\])')
		matches = items_pattern.findall(response_data)
	
		all_items = []
		for match in matches:
			try:
				items = json.loads(match)
				all_items.extend(items)
			except json.JSONDecodeError:
				self.logger.warning(f'Failed to parse items JSON: {match}')
	
		return all_items
	
logging.getLogger('monday_client').addHandler(logging.NullHandler())