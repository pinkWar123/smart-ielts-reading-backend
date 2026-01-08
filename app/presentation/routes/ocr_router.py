from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.application.use_cases.tests.queries.extract_test.extract_test_from_images.extract_test_from_images_dto import (
    ExtractedTestResponse,
    ImagesExtractRequest,
)
from app.common.dependencies import OcrUseCases, get_ocr_use_cases

router = APIRouter()


@router.post("/extract-text")
async def extract_text_from_image(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    use_cases: OcrUseCases = Depends(get_ocr_use_cases),
):
    """Extract text from an uploaded image using OCR."""
    file_content = await file.read()
    text = await use_cases.extract_text.execute(
        file_content, prompt, content_type=file.content_type
    )
    return {"filename": file.filename, "extracted_text": text, "prompt_used": prompt}


@router.post("/extract-test", response_model=ExtractedTestResponse)
async def extract_test_from_images(
    files: List[UploadFile] = File(
        ..., description="List of images to extract test from"
    ),
    test_title: Optional[str] = Form(
        None, description="Optional title hint for the test"
    ),
    extraction_hint: Optional[str] = Form(
        None, description="Optional extraction hints for the test"
    ),
    use_cases: OcrUseCases = Depends(get_ocr_use_cases),
):
    images: List[bytes] = [await file.read() for file in files]
    request: ImagesExtractRequest = ImagesExtractRequest(
        images=images, test_title=test_title, extraction_hints=extraction_hint
    )
    return await use_cases.extract_test.execute(request)
