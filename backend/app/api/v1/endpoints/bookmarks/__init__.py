from fastapi import APIRouter

from app.api.v1.endpoints.bookmarks import crud

router = APIRouter()

# Include all endpoint routers
router.include_router(crud.router, tags=["bookmarks"])
