from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.application.services.query.passages.passages_query_model import (
    AuthorInfo,
    PassageDetail,
)
from app.application.services.query.passages.passages_query_service import (
    PassagesQueryService,
)
from app.domain.errors.passage_errors import PassageNotFoundError
from app.infrastructure.persistence.models import (
    PassageModel,
    QuestionGroupModel,
    UserModel,
)


class SqlPassageQueryService(PassagesQueryService):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_passage_detail_by_id(self, passage_id: str) -> PassageDetail:
        stmt = (
            select(PassageModel, UserModel)
            .options(
                selectinload(PassageModel.question_groups).selectinload(
                    QuestionGroupModel.questions
                )
            )
            .join(UserModel, PassageModel.created_by == UserModel.id, isouter=True)
            .where(PassageModel.id == passage_id)
        )

        resultset = await self.session.execute(stmt)
        try:
            result = resultset.one()
        except Exception as e:
            print(e)
            raise PassageNotFoundError(passage_id)

        passage_model: PassageModel = result[0]
        passage = passage_model.to_domain()
        user_model: UserModel = result[1]

        response = PassageDetail(
            id=passage.id,
            title=passage.title,
            content=passage.content,
            word_count=passage.word_count,
            difficulty_level=passage.difficulty_level,
            topic=passage.topic,
            source=passage.source,
            created_by=AuthorInfo(
                id=user_model.id,
                username=user_model.username,
                full_name=user_model.full_name,
                email=user_model.email,
            ),
            is_active=passage.is_active,
            question_groups=passage.question_groups,
            created_at=passage.created_at,
        )

        return response
