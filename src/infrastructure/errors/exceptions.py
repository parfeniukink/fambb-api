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


class UnprocessableRequestError(BaseError):
    """consider cases when the server can not perform the operation due
    wrong request from the user.

    notes:
        if `BadRequestError(400)` is raised in case user input data can't be
            validated or something else, the `UnprocessableRequestError(422)`
            is raised only if the input data is properly set, but system CAN
            NOT change its state because of any reasons. let's say you'd like
            to user some sort of INSERT command but due to the duplication in
            the database the operation can't be performed.

            using another explaination: if HTTP POST /resource returns 400, it
            is going to return 400 Bad Request all the time. Otherwise, if
            HTTP POST /resource returns 200 OK, it may return 422 Unprocessable
            Entity for the second request and again 200 OK for the 3-rd request
            if the business logic doesn't mind.

    """

    def __init__(self, message="Unprocessable entity") -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
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
