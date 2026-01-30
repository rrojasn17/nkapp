from pydantic import BaseModel
from typing import Optional

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
