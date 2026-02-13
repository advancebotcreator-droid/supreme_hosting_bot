from aiogram import Router
from .start import router as start_router
from .upload import router as upload_router
from .process import router as process_router
from .admin import router as admin_router
from .owner import router as owner_router
from .premium import router as premium_router
from .install import router as install_router


def get_all_routers() -> list[Router]:
    return [
        start_router,
        owner_router,   # Owner first for priority
        admin_router,
        premium_router,
        upload_router,
        process_router,
        install_router,
    ]
