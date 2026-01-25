from app.application.use_cases.base.use_case import (
    AuthenticatedUseCase,
    RequestType,
    ResponseType,
)
from app.application.use_cases.tests.commands.unpublish_test.unpublish_test_dto import (
    UnpublishTestCommand,
    UnpublishTestResponse,
)
from app.domain.aggregates.users.user import UserRole
from app.domain.repositories.attempt_repository import AttemptRepositoryInterface
from app.domain.repositories.test_repository import TestRepositoryInterface
from app.domain.repositories.user_repository import UserRepositoryInterface


class UnpublishTestUseCase(
    AuthenticatedUseCase[UnpublishTestCommand, UnpublishTestResponse]
):
    def __init__(
        self,
        test_repo: TestRepositoryInterface,
        attempt_repo: AttemptRepositoryInterface,
        user_repo: UserRepositoryInterface,
    ):
        self.test_repo = test_repo
        self.attempt_repo = attempt_repo
        self.user_repo = user_repo

    async def execute(
        self, request: UnpublishTestCommand, user_id: str
    ) -> UnpublishTestResponse:
        # Get the test
        test = await self.test_repo.get_by_id(request.id)
        if not test:
            return UnpublishTestResponse(
                success=False, message=f"Test with id {request.id} not found"
            )

        # Check authorization: must be admin or the teacher who created the test
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return UnpublishTestResponse(success=False, message="User not found")

        if user.role != UserRole.ADMIN and test.created_by != user_id:
            return UnpublishTestResponse(
                success=False,
                message="Unauthorized. Only admins or the test creator can unpublish this test",
            )

        # Check if the test is already unpublished
        if not test.is_published:
            return UnpublishTestResponse(
                success=False,
                message=f"Test with id {request.id} is already unpublished",
            )

        # Check if test has any attempts
        attempts = await self.attempt_repo.get_by_test(request.id)
        if attempts:
            return UnpublishTestResponse(
                success=False,
                message=f"Cannot unpublish test. It has been taken by {len(attempts)} user(s)",
            )

        # Unpublish the test
        test.unpublish()
        await self.test_repo.update(test)

        return UnpublishTestResponse(
            success=True, message=f"Test {request.id} unpublished successfully"
        )
