from fastapi import APIRouter, Depends
from .docs import router as docs_router

# router = APIRouter(dependencies=[Depends(dependencies.authorize_user)]) # noqa: E800

router = APIRouter()

router.include_router(docs_router, prefix='/docs')
