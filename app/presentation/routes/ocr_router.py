from typing import Optional

from dependency_injector.wiring import Provider
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.common.di import make_service_dependency
from app.container import ApplicationContainer
from app.presentation.controllers.ocr_controller import OcrController

router = APIRouter()

get_ocr_controller = make_service_dependency(
    Provider[ApplicationContainer.ocr_controller]
)


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
