from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.application.use_cases.tests.extract_test.extract_test_from_images.extract_test_from_images_dto import (
    ExtractedTestResponse,
    ImagesExtractRequest,
)
from app.application.use_cases.tests.extract_test.extract_test_from_images.extract_test_from_images_use_case import (
    ExtractTestFromImagesUseCase,
)
from app.common.dependencies import (
    get_extract_test_from_images_use_case,
    get_ocr_controller,
)
from app.presentation.controllers.ocr_controller import OcrController

router = APIRouter()


@router.post("/extract-text")
async def extract_text_from_image(
    file: UploadFile = File(...),
    prompt: Optional[str] = Form(None),
    controller: OcrController = Depends(get_ocr_controller),
):
    """Extract text from an uploaded image using OCR."""
    try:
        return await controller.extract_text_from_image(file, prompt)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
    use_case: ExtractTestFromImagesUseCase = Depends(
        get_extract_test_from_images_use_case
    ),
):
    images: List[bytes] = [await file.read() for file in files]
    request: ImagesExtractRequest = ImagesExtractRequest(
        images=images, test_title=test_title, extraction_hints=extraction_hint
    )
    return await use_case.execute(request)
