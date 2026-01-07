"""Test Query Service Interface

This service is responsible for read operations that require data from multiple aggregates.
Unlike repositories which return domain entities, query services return read-optimized DTOs.

This follows CQRS-lite pattern: repositories for writes, query services for reads.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from app.application.services.query.tests.test_query_model import (
    TestWithAuthorQueryModel,
    TestWithDetailsQueryModel,
    TestWithPassagesQueryModel,
)
from app.domain.aggregates.test.test_status import TestStatus
from app.domain.aggregates.test.test_type import TestType


class TestQueryService(ABC):
    """
    Query service for test read operations.

    This service can perform optimized queries (like JOINs) and return denormalized data
    without affecting the purity of domain entities and repositories.
    """

    @abstractmethod
    async def get_all_with_authors(
        self,
        status: Optional[TestStatus] = None,
        test_type: Optional[TestType] = None,
    ) -> List[TestWithAuthorQueryModel]:
        """
        Get all tests with author information using a single optimized query.

        Args:
            status: Optional filter by test status
            test_type: Optional filter by test type

        Returns:
            List of tests with enriched author data
        """
        pass

    @abstractmethod
    async def get_test_by_id_with_passages(
        self,
        test_id: str,
        status: Optional[TestStatus] = None,
        test_type: Optional[TestType] = None,
    ) -> TestWithPassagesQueryModel:
        """
        Get all tests with author information using a single optimized query.

        Args:
            status: Optional filter by test status
            test_type: Optional filter by test type

        Returns:
            List of tests with enriched author data
            :param test_type:
            :param status:
            :param test_id:
        """
        pass

    @abstractmethod
    async def get_test_by_id_with_details(
        self, test_id: str
    ) -> TestWithDetailsQueryModel:
        pass
