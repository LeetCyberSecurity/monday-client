from ...exceptions import MondayAPIError


def check_query_result(query_result):
    if isinstance(query_result, dict) and any('error' in key.lower() for key in query_result.keys()):
        raise MondayAPIError(f"API request failed: {query_result['error']}", json_data=query_result['error'])
    if 'data' not in query_result:
        raise MondayAPIError(f"Unexpected API response: {query_result}")
    return query_result
