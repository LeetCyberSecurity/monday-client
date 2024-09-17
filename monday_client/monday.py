import json
import logging
import re
import time
from threading import Lock
from typing import Any, Dict, List, Mapping, Optional, Union

import requests
from ratelimit import limits, sleep_and_retry
from tenacity import (retry, retry_if_exception_type, stop_after_attempt,
                      wait_fixed)


class ComplexityLimitExceeded(Exception):
	"""
	Exception raised when the complexity limit is exceeded.

	Attributes:
		message (str): Explanation of the error.
		reset_in (int): Time in seconds until the complexity limit is reset.
	"""
	def __init__(self, message, reset_in):
		super().__init__(message)
		self.reset_in = reset_in

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

	def __init__(self, api_key: str):
		"""
		Initialize the MondayClient with the provided API key.

		Args:
			api_key (str): The API key for authenticating with the Monday.com API.
		"""
		self.url = 'https://api.monday.com/v2'
		self.headers = {'Content-Type': 'application/json', 'Authorization': f'{api_key}'}
		# monday.com rate limits:
		# https://developer.monday.com/api-reference/docs/rate-limits
		self.complexity_limit = 10000000 # 10M combined read/write complexity per minute
		self.period = 60
		self.mutation_limit = 2000 # 2000 mutations per minute
		self.special_mutation_limit = 40 # 40 "special" mutations per minute
		self.special_mutations = ['duplicate_group', 'create_board', 'duplicate_board']
		self.valid_query_types = ['query', 'mutation']
		self._complexity_used = 0
		self._mutations_used = 0
		self._special_mutations_used = 0
		self._lock = Lock()
		self._last_reset = time.time()
		self._mutations_last_reset = time.time()
		self._special_mutations_last_reset = time.time()

	def items_page(self, board_id: int, query_params: str = '', limit: int = 25, fields: str = 'id name column_values { id text value column { title } }') -> Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]:
		"""
		Retrieves a paginated list of items from a specified board on Monday.com.

		Args:
			board_id (int): The ID of the board from which to retrieve items.
			query_params (str, optional): Additional query parameters to filter the items. Defaults to None.
			limit (int, optional): The maximum number of items to retrieve per page. Defaults to 25.
			fields (str, optional): The fields to include in the response. Defaults to 'id name column_values { id text value column { title } }'.

		Returns:
			Dict[str, bool | List[Dict[str, Any]] | str | None]: A dictionary containing the combined items retrieved
			and a completion status. 
			The dictionary has the following structure:
				
				- 'items': A list of dictionaries representing the items retrieved.
				- 'completed': A boolean indicating whether the pagination was completed successfully.
		"""
		if query_params:
			query = f'boards (ids: {board_id}) {{ items_page (limit: {limit}, query_params: {query_params}) {{ cursor items {{ {fields} }} }} }}'
		else:
			query = f'boards (ids: {board_id}) {{ items_page (limit: {limit}) {{ cursor items {{ {fields} }} }} }}'
		return self.paginated_item_request(query, 'query')

	def paginated_item_request(self, query: str, query_type: str) -> Dict[str, Union[bool, List[Dict[str, Any]], Optional[str]]]:
		"""
		Executes a paginated request to retrieve items from Monday.com.

		This method handles the pagination logic to retrieve all items from a board
		by repeatedly querying the API until all items are fetched.

		Args:
			query (str): The GraphQL query string to be executed.
			query_type (str): The type of the query, either 'query' or 'mutation'.

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
				paginated_query = f'next_items_page (limit: 50, cursor: "{cursor}") {{ cursor {items_value} }}'

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
				sleep_time = exception.reset_in
				time.sleep(sleep_time)

	@retry(
		stop=stop_after_attempt(4),
		retry=retry_if_exception_type(ComplexityLimitExceeded),
		wait=wait_fixed(1),
		before_sleep=_sleep_before_retry,
		reraise=True
	)
	@sleep_and_retry
	@limits(calls=5000, period=60) # 5000 requests per minute per IP
	def _execute_post_request(self, query: str, query_type: str) -> Union[Dict[str, Any], bool]:
		"""
		Executes a post request to the Monday.com API with rate limiting and retry logic.

		Args:
			query (str): The GraphQL query string to be executed.
			query_type (str): The type of the query, either 'query' or 'mutation'.

		Returns:
			Dict[str, Any]: The response data from the API.
		"""
		query_type = query_type.lower()
		if query_type not in self.valid_query_types:
			self.logger.error(f'invalid query type: {query_type}')
			return {'error': 'Invalid query type'}

		query = f'{query_type} {{ complexity {{ before after query reset_in_x_seconds }} {query} }}'
		self.logger.info(f'submitting query: {query}')
		response = requests.post(self.url, json={'query': query}, headers=self.headers)
		response_data = response.json()
		self.logger.debug(f'response to query {query}: {response_data}')

		if 'errors' in response_data:
			error_message = response_data['errors'][0]['message']
			self.logger.error(f'GraphQL error: {error_message}')
			return {'error': error_message}
		
		with self._lock:
			try:
				complexity = response_data['data']['complexity']
			except KeyError:
				self.logger.error(f'error getting complexity: {response_data}')
				return {'error': response_data}
			complexity_before = complexity['before']
			complexity_after = complexity['after']
			complexity_used = complexity_before - complexity_after
			reset_in = complexity['reset_in_x_seconds']

			# Check if complexity has been reset
			if complexity_after > self._complexity_used:
				self.logger.info('Complexity limit has been reset')
				self._complexity_used = 0

			if self._complexity_used + complexity_used > self.complexity_limit - 1000:
				self.logger.info(f'Complexity limit exceeded. Resetting complexity used.')
				self._complexity_used = 0
				raise ComplexityLimitExceeded(f'Complexity limit exceeded, retrying after {reset_in} seconds...', reset_in)

			self._complexity_used += complexity_used

			if query_type == 'mutation':
				mutation_name = self._extract_mutation_name(query)
				if mutation_name in self.special_mutations:
					self._check_special_mutation_limit()
				else:
					self._check_mutation_limit()

		return response_data or False

	def _check_mutation_limit(self):
		"""
		Checks and enforces the mutation limit for the API.

		If the mutation limit is reached, the method will sleep until the limit is reset.
		"""
		current_time = time.time()
		if current_time - self._mutations_last_reset >= 60:
			self._mutations_used = 0
			self._mutations_last_reset = current_time

		self._mutations_used += 1
		if self._mutations_used >= self.mutation_limit:  # Changed > to >=
			sleep_time = 60 - (current_time - self._mutations_last_reset)
			if sleep_time > 0:
				self.logger.info(f'Mutation limit reached. Sleeping for {sleep_time} seconds.')
				time.sleep(sleep_time)
			self._mutations_used = 1
			self._mutations_last_reset = current_time

		# Add this line for debugging
		print(f"Mutations used: {self._mutations_used}")

	def _check_special_mutation_limit(self):
		"""
		Checks and enforces the special mutation limit for the API.

		If the special mutation limit is reached, the method will sleep until the limit is reset.
		"""
		current_time = time.time()
		if current_time - self._special_mutations_last_reset >= 60:
			self._special_mutations_used = 0
			self._special_mutations_last_reset = current_time

		self._special_mutations_used += 1
		if self._special_mutations_used >= self.special_mutation_limit:
			sleep_time = 60 - (current_time - self._special_mutations_last_reset)
			if sleep_time > 0:
				self.logger.info(f'Special mutation limit reached. Sleeping for {sleep_time} seconds.')
				time.sleep(sleep_time)
			self._special_mutations_used = 1
			self._special_mutations_last_reset = current_time

	def _extract_mutation_name(self, query: str) -> Optional[str]:
		"""
		Extracts the mutation name from a GraphQL query string.

		Args:
			query (str): The GraphQL query string.

		Returns:
			Optional[str]: The name of the mutation if it can be extracted, otherwise None.
		"""
		mutation_pattern = re.compile(r'mutation\s*{.*?}\s*{?\s*(\w+)')
		match = mutation_pattern.search(query)
		if match:
			return match.group(1)
		else:
			self.logger.warning(f'Could not extract mutation name from query: {query}')
			return None
		
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