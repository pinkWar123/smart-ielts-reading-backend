from abc import ABC, abstractmethod
from typing import Generic, TypeVar

RequestType = TypeVar("RequestType")
ResponseType = TypeVar("ResponseType")


class UseCase(ABC, Generic[RequestType, ResponseType]):
    """Base interface for all use cases."""

    @abstractmethod
    def execute(self, request: RequestType) -> ResponseType:
        """Execute the use case with the given request and return a response."""
        pass


class SimpleUseCase(ABC):
    """Use case interface for operations with no input or output."""

    @abstractmethod
    def execute(self) -> None:
        """Execute a use case with no input or output."""
        pass


class QueryUseCase(ABC, Generic[ResponseType]):
    """Use case interface for query operations that return data but take no input."""

    @abstractmethod
    def execute(self) -> ResponseType:
        """Execute a query use case that returns data but takes no input."""
        pass


class CommandUseCase(ABC, Generic[RequestType]):
    """Use case interface for command operations that take input but return nothing."""

    @abstractmethod
    def execute(self, request: RequestType) -> None:
        """Execute a command use case that takes input but returns nothing."""
        pass
