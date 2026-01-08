import asyncio
import json
from abc import ABC

from anthropic import AsyncAnthropic

from app.application.services.test_generator_service import ITestGeneratorService
from app.application.use_cases.tests.queries.extract_test.extract_test_from_images.extract_test_from_images_dto import (
    ExtractedCorrectAnswer,
    ExtractedOption,
    ExtractedPassage,
    ExtractedQuestion,
    ExtractedQuestionGroup,
    ExtractedTestResponse,
    TestMetadata,
)
from app.common.settings import Settings
from app.domain.entities.question import QuestionType
from app.domain.entities.test import TestType


class ClaudeTestGeneratorService(ITestGeneratorService, ABC):
    def __init__(self, settings: Settings, client: AsyncAnthropic):
        self.settings = settings
        self.client = client

    async def generate_test(self, prompt: str) -> ExtractedTestResponse:
        for attempt in range(self.settings.max_retry_attempts):
            try:
                response = await self.client.messages.create(
                    model=self.settings.claude_model,
                    max_tokens=8000,
                    messages=[{"role": "user", "content": prompt}],
                )

                response_text = response.content[0].text.strip()

                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                    response_text = response_text.strip()

                data = json.loads(response_text)
                print(data)
                return self._parse_response(data)
            except json.JSONDecodeError as e:
                if attempt == self.settings.max_retry_attempts - 1:
                    raise ValueError(f"Failed to parse Claude response as JSON: {e}")
                await asyncio.sleep(2**attempt)

            except Exception as e:
                if attempt == self.settings.max_retry_attempts - 1:
                    raise Exception(
                        f"Failed to extract test after {self.settings.max_retry_attempts} attempts: {e}"
                    )
                await asyncio.sleep(2**attempt)

    def _parse_response(self, data: dict) -> ExtractedTestResponse:
        """Parse Claude response into ExtractedTestResponse matching our system format"""
        passages = []

        for passage_data in data.get("passages", []):
            # Parse question groups
            question_groups = []
            for group_data in passage_data.get("question_groups", []):
                # Parse group-level options if present
                group_options = None
                if group_data.get("options"):
                    group_options = [
                        ExtractedOption(label=opt["label"], text=opt["text"])
                        for opt in group_data["options"]
                    ]

                question_group = ExtractedQuestionGroup(
                    id=group_data["id"],
                    group_instructions=group_data["group_instructions"],
                    question_type=QuestionType(group_data["question_type"]),
                    start_question_number=group_data["start_question_number"],
                    end_question_number=group_data["end_question_number"],
                    order_in_passage=group_data["order_in_passage"],
                    options=group_options,
                )
                question_groups.append(question_group)

            # Parse questions
            questions = []
            for q_data in passage_data.get("questions", []):
                # Parse options if present
                options = None
                if q_data.get("options"):
                    options = [
                        ExtractedOption(label=opt["label"], text=opt["text"])
                        for opt in q_data["options"]
                    ]

                # Parse correct answer
                correct_answer_data = q_data.get("correct_answer", {})
                correct_answer = ExtractedCorrectAnswer(
                    answer=correct_answer_data.get("answer"),
                    acceptable_answers=correct_answer_data.get(
                        "acceptable_answers", []
                    ),
                )

                question = ExtractedQuestion(
                    question_number=q_data["question_number"],
                    question_type=QuestionType(q_data["question_type"]),
                    question_text=q_data["question_text"],
                    options=options,
                    correct_answer=correct_answer,
                    explanation=q_data.get("explanation"),
                    instructions=q_data.get("instructions"),
                    points=q_data.get("points", 1),
                    order_in_passage=q_data["order_in_passage"],
                    question_group_id=q_data.get("question_group_id"),
                )
                questions.append(question)

            # Create passage
            passage = ExtractedPassage(
                title=passage_data["title"],
                content=passage_data["content"],
                difficulty_level=passage_data.get("difficulty_level", 1),
                topic=passage_data["topic"],
                source=passage_data.get("source"),
                question_groups=question_groups,
                questions=questions,
            )
            passages.append(passage)

        # Parse test metadata
        metadata_data = data.get("test_metadata", {})
        test_metadata = TestMetadata(
            title=metadata_data.get("title"),
            description=metadata_data.get("description"),
            total_questions=metadata_data.get("total_questions", 0),
            estimated_time_minutes=metadata_data.get("estimated_time_minutes", 60),
            test_type=TestType(metadata_data.get("test_type", "FULL_TEST")),
        )

        return ExtractedTestResponse(
            passages=passages,
            test_metadata=test_metadata,
            extraction_notes=data.get("extraction_notes", []),
            confidence_score=data.get("confidence_score"),
        )
