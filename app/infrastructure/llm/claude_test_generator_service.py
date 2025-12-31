import asyncio
import json
from abc import ABC

from anthropic import AsyncAnthropic

from app.application.services.test_generator_service import ITestGeneratorService
from app.application.use_cases.tests.extract_test.extract_test_from_images.extract_test_from_images_dto import (
    ExtractedOption,
    ExtractedPassage,
    ExtractedQuestion,
    ExtractedQuestionGroup,
    ExtractedQuestionType,
    ExtractedTestResponse,
    ExtractedTestSection,
)
from app.common.settings import Settings


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
        sections = []

        for section_data in data.get("sections", []):
            passage_data = section_data.get("passage", {})
            passage = ExtractedPassage(
                title=passage_data.get("title"),
                content=passage_data.get("content", ""),
                paragraphs=passage_data.get("paragraphs"),
                word_count=passage_data.get("word_count"),
                source_image_index=passage_data.get("source_image_index", 0),
            )

            question_groups = []
            for group_data in section_data.get("question_groups", []):
                questions = []
                for q_data in group_data.get("questions", []):
                    options = None
                    if q_data.get("options"):
                        options = [
                            ExtractedOption(label=opt["label"], text=opt["text"])
                            for opt in q_data["options"]
                        ]

                    question = ExtractedQuestion(
                        question_number=q_data["question_number"],
                        question_type=ExtractedQuestionType(q_data["question_type"]),
                        question_text=q_data["question_text"],
                        options=options,
                        correct_answer=q_data.get("correct_answer"),
                        explanation=q_data.get("explanation"),
                        instructions=q_data.get("instructions"),
                    )
                    questions.append(question)

                question_group = ExtractedQuestionGroup(
                    group_instructions=group_data["group_instructions"],
                    question_type=ExtractedQuestionType(group_data["question_type"]),
                    questions=questions,
                    start_question_number=group_data["start_question_number"],
                    end_question_number=group_data["end_question_number"],
                )
                question_groups.append(question_group)

            section = ExtractedTestSection(
                passage=passage,
                question_groups=question_groups,
                total_questions=section_data.get("total_questions", 0),
            )
            sections.append(section)

        return ExtractedTestResponse(
            title=data.get("title"),
            description=data.get("description"),
            sections=sections,
            total_questions=data.get("total_questions", 0),
            estimated_time_minutes=data.get("estimated_time_minutes", 60),
            extraction_notes=data.get("extraction_notes"),
            confidence_score=data.get("confidence_score"),
        )
