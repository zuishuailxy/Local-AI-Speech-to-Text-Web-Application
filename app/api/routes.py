from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    """Liveness/readiness probe required by the assessment."""

    return {"status": "ok"}
