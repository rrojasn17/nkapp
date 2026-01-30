from .health import router as health_router
from .auth import router as auth_router
from .unidades_productivas import router as unidades_router
from .dispositivos import router as dispositivos_router
from .ttn import router as ttn_router
from .datos import router as datos_router

__all__ = [
    "health_router",
    "auth_router",
    "unidades_router",
    "dispositivos_router",
    "ttn_router",
    "datos_router",
]
