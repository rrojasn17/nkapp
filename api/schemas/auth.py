from pydantic import BaseModel
from typing import Optional

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
