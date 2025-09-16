from fastapi import APIRouter

from app.api.v1.endpoints.applications import crud

router = APIRouter()

# Include all endpoint routers
router.include_router(crud.router, tags=["applications"])
