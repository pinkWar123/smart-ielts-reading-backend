from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.db.engine import close_database, initialize_database
from app.common.settings import settings
from app.container import container
from app.presentation.exception.global_exception_handler import setup_exception_handlers
from app.presentation.routes.auth_router import router as auth_router
from app.presentation.routes.class_router import router as class_router
from app.presentation.routes.ocr_router import router as ocr_router
from app.presentation.routes.passage_router import router as passage_router
from app.presentation.routes.test_router import router as test_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_database()
    container.wire(
        modules=[
            "app.presentation.routes.passage_router",
            "app.presentation.routes.test_router",
            "app.presentation.routes.auth_router",
            "app.presentation.routes.ocr_router",
            "app.common.di",
        ]
    )
    yield
    # Shutdown
    await close_database()


app = FastAPI(lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Other Middlewares
setup_exception_handlers(app)

v1_router = APIRouter(prefix="/api/v1")


@v1_router.get("/health")
def health_check():
    return "OK"


v1_router.include_router(passage_router, prefix="/passages", tags=["Passages"])
v1_router.include_router(test_router, prefix="/tests", tags=["Tests"])
v1_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
v1_router.include_router(ocr_router, prefix="/ocr", tags=["OCR"])
v1_router.include_router(class_router, prefix="/classes", tags=["Classes"])

app.include_router(v1_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
