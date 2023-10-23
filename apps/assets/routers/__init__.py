from fastapi import APIRouter

from .assets import router as asset_router
from .accounts import router as account_router
from .workers import router as worker_router


router = APIRouter(prefix='/assets')

router.include_router(asset_router)
router.include_router(account_router)
router.include_router(worker_router)
