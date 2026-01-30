from pydantic import BaseModel
from typing import Optional

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
