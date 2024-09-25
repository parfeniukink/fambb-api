from fastapi import status


class BaseError(Exception):
    def __init__(
        self,
        message="Unhandled error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    ) -> None:
        """the base class for all errors."""

        self.message: str = message
        self.status_code: int = status_code

        super().__init__(message)


class BadRequestError(BaseError):
    """consider cases when the server can not perform the operation due
    wrong request from the user.
    """

    def __init__(self, message="Bad request") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class NotFoundError(BaseError):
    """consider cases when the resourse can't be found for this operation."""

    def __init__(self, message="Not found") -> None:
        super().__init__(
            message=message, status_code=status.HTTP_404_NOT_FOUND
        )


class AuthenticationError(BaseError):
    def __init__(self, message="Not authenticated") -> None:
        """Consider any case the user wants to perform an action
        but correct credentials were not provided.
        """

        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class DatabaseError(BaseError):
    def __init__(self, message="Database error") -> None:
        """Any internally defined database error
        have to raise this exception.
        """

        super().__init__(message=message)
