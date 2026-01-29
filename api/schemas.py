from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, List
from datetime import datetime


# =========================================================
# TTN
# =========================================================
class TTNWebhookIn(BaseModel):
    raw: Dict[str, Any] = Field(default_factory=dict)


# =========================================================
# AUTH
# =========================================================
class RegistroUsuarioIn(BaseModel):
    nombre: str
    correo: str
    rol: Optional[str] = "usuario"


class RegistroUsuarioOut(BaseModel):
    usuario_id: int
    correo: str
    contrasena_temporal: Optional[str] = None
    token: str


class LoginIn(BaseModel):
    correo: str
    password: str


class LoginOut(BaseModel):
    token: str


class ResetRequestIn(BaseModel):
    correo: str


class ResetRequestOut(BaseModel):
    mensaje: str
    token_restablecimiento: Optional[str] = None


class ResetConfirmIn(BaseModel):
    token_restablecimiento: str
    nueva_contrasena: str


class ResetConfirmOut(BaseModel):
    mensaje: str


# =========================================================
# UNIDADES PRODUCTIVAS
# =========================================================
class UnidadProductivaCreateIn(BaseModel):
    nombre: str
    area: Optional[float] = None
    descripcion: Optional[str] = None
    cualidades: Optional[str] = None
    tipo: Optional[str] = None
    categoria: Optional[str] = None
    direccion: Optional[str] = None
    georreferenciacion: Optional[str] = None


class UnidadProductivaOut(BaseModel):
    id: int
    usuario_id: int
    nombre: str
    area: Optional[float] = None
    descripcion: Optional[str] = None
    cualidades: Optional[str] = None
    tipo: Optional[str] = None
    categoria: Optional[str] = None
    direccion: Optional[str] = None
    georreferenciacion: Optional[str] = None

    class Config:
        from_attributes = True


# =========================================================
# DISPOSITIVOS
# =========================================================
class DispositivoCreateIn(BaseModel):
    unidad_productiva_id: int
    marca: Optional[str] = None
    identificador_dispositivo: Optional[str] = None
    tipo: Optional[str] = None
    eui: str


class DispositivoOut(BaseModel):
    id: int
    usuario_id: int
    unidad_productiva_id: int
    marca: Optional[str] = None
    identificador_dispositivo: Optional[str] = None
    tipo: Optional[str] = None
    eui: str

    class Config:
        from_attributes = True


# =========================================================
# DATOS
# =========================================================
class ItemDatoOut(BaseModel):
    eui: str
    dispositivo_id: int
    fecha_hora: datetime
    origen: str
    nombre_variable: str
    ruta_variable: Optional[str] = None
    unidad: Optional[str] = None
    valor: float


class ConsultaDatosOut(BaseModel):
    items: List[ItemDatoOut]
