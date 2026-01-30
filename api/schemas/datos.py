from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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
