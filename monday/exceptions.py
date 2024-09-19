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

class QueryFormatError(Exception):
    """
    Exception raised when a query is improperly formatted.

    Attributes:
        message (str): Explanation of the error.
    """
    def __init__(self, message: str):
        super().__init__(message)

class PaginationError(Exception):
    """
    Exception raised when item pagination fails.

    Attributes:
        message (str): Explanation of the error.
    """
    def __init__(self, message: str):
        super().__init__(message)