import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from config import CORS_ORIGINS

# IMPORTANTE: esto fuerza a que SQLAlchemy "registre" los modelos
# antes de create_all (si no, create_all crea 0 tablas).
from models import Usuario, UnidadProductiva, Dispositivo, Dato, ValorDato  # noqa: F401

from routers import (
    health_router,
    auth_router,
    unidades_router,
    dispositivos_router,
    ttn_router,
    datos_router,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(title="Ingesta TTN + API (Producción-ready)")

# CORS configurable por variables de entorno
if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# MVP: crear tablas (en producción: Alembic)
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(unidades_router)
app.include_router(dispositivos_router)
app.include_router(ttn_router)
app.include_router(datos_router)
