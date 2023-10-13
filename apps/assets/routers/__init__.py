from fastapi import APIRouter

from .assets import router as asset_router
from .platforms import router as platform_router
from .accounts import router as account_router


router = APIRouter(prefix='/assets')

router.include_router(asset_router)
router.include_router(platform_router)
router.include_router(account_router)
