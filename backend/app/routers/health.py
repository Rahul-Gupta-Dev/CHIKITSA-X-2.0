from fastapi import APIRouter
from app.schemas import HealthResponse

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/health", response_model=HealthResponse)
def health_check():
    return {
        "status": "ok",
        "service": "CHIKITSAX backend"
    }
