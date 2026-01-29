import secrets
from passlib.context import CryptContext

_contexto_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generar_token() -> str:
    return secrets.token_urlsafe(32)


def generar_contrasena_temporal(longitud: int = 12) -> str:
    return secrets.token_urlsafe(32)[:longitud]


def generar_token_restablecimiento() -> str:
    return secrets.token_urlsafe(32)


def hashear_contrasena(contrasena: str) -> str:
    return _contexto_pwd.hash(contrasena)


def verificar_contrasena(contrasena: str, hash_contrasena: str) -> bool:
    return _contexto_pwd.verify(contrasena, hash_contrasena)
