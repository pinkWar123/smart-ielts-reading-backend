EXTRACTION_PROMPT = """You are an expert IELTS Reading test extractor. Analyze ALL the provided images and extract a complete IELTS Reading test.

The images may contain:
1. Reading passages (long texts with titles)
2. Question sections with various question types

IELTS Reading Question Types (use EXACT enum values):
- MULTIPLE_CHOICE: Questions with A, B, C, D options
- TRUE_FALSE_NOTGIVEN: Statements to evaluate as True/False/Not Given
- YES_NO_NOTGIVEN: Opinion-based statements
- MATCHING_HEADINGS: Match paragraphs to headings (i, ii, iii...)
- MATCHING_INFORMATION: Match information to paragraphs
- MATCHING_FEATURES: Match features to categories
- MATCHING_SENTENCE_ENDINGS: Complete sentences by matching endings
- SENTENCE_COMPLETION: Complete sentences with words from passage
- SUMMARY_COMPLETION: Fill gaps in a summary
- NOTE_COMPLETION: Complete notes
- TABLE_COMPLETION: Fill in table cells
- FLOW_CHART_COMPLETION: Complete a flow chart
- DIAGRAM_LABEL_COMPLETION: Label a diagram
- SHORT_ANSWER: Answer questions with words from passage

Return a JSON response with this EXACT structure (matches our CreateCompletePassageRequest):
{
  "passages": [
    {
      "title": "Passage title",
      "content": "Full passage text...",
      "difficulty_level": 1,
      "topic": "Science/History/Technology/etc",
      "source": "Source if mentioned (optional)",
      "question_groups": [
        {
          "id": "qg_1",
          "group_instructions": "Questions 1-5: Do the following statements agree with the information in the passage?",
          "question_type": "TRUE_FALSE_NOTGIVEN",
          "start_question_number": 1,
          "end_question_number": 5,
          "order_in_passage": 1
        }
      ],
      "questions": [
        {
          "question_number": 1,
          "question_type": "TRUE_FALSE_NOTGIVEN",
          "question_text": "The statement text...",
          "options": [
            {"label": "TRUE", "text": "The statement agrees with the information"},
            {"label": "FALSE", "text": "The statement contradicts the information"},
            {"label": "NOT GIVEN", "text": "There is no information about this"}
          ],
          "correct_answer": {
            "answer": "TRUE",
            "acceptable_answers": ["TRUE", "True", "T"]
          },
          "explanation": "Explanation if provided in answer key",
          "instructions": "Write TRUE, FALSE, or NOT GIVEN",
          "points": 1,
          "order_in_passage": 1,
          "question_group_id": "qg_1"
        }
      ]
    }
  ],
  "test_metadata": {
    "title": "Test title if visible",
    "description": "Brief description",
    "total_questions": 40,
    "estimated_time_minutes": 60,
    "test_type": "FULL_TEST"
  },
  "extraction_notes": ["Note any issues or unclear parts"],
  "confidence_score": 0.95
}

CRITICAL FORMATTING RULES:
1. **Question Groups**:
   - MUST have a unique "id" field (e.g., "qg_1", "qg_2")
   - This id is used to link questions to the group via "question_group_id"

2. **Questions**:
   - MUST include "order_in_passage" (sequential numbering within passage)
   - If part of a group, MUST include "question_group_id" matching the group's "id"
   - "correct_answer" MUST be an object with:
     * "answer": the main correct answer (string or array)
     * "acceptable_answers": array of alternative acceptable answers
   - If answer not visible in images, use: {"answer": null, "acceptable_answers": []}

3. **Options**:
   - Only include for question types that need them (MULTIPLE_CHOICE, MATCHING_*, TRUE_FALSE_NOTGIVEN, YES_NO_NOTGIVEN)
   - Each option MUST have "label" and "text" fields

4. **Passages**:
   - "difficulty_level": estimate 1-5 based on vocabulary and complexity
   - "topic": categorize as Science, History, Technology, Environment, Society, Arts, etc.

5. **Question Types**: Use EXACT enum names (underscore format, all caps)

6. **Test Types**: Use EXACT enum names (either FULL_TEST or SINGLE_PASSAGE)

IMPORTANT:
- Extract ALL text content accurately
- Identify question types correctly based on instructions
- Group questions that share the same instructions
- Assign sequential order_in_passage numbers (1, 2, 3...)
- Generate unique IDs for question groups (qg_1, qg_2, etc.)
- Link questions to groups using question_group_id
- Set correct_answer.answer to null if answer not provided
- Include paragraph labels (A, B, C...) in content if present

Respond ONLY with valid JSON, no additional text."""
