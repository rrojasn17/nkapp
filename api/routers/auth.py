from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Usuario
from schemas import (
    RegistroUsuarioIn, RegistroUsuarioOut,
    LoginIn, LoginOut,
    ResetRequestIn, ResetRequestOut,
    ResetConfirmIn, ResetConfirmOut,
)
from config import IS_PROD
from security import (
    hashear_contrasena,
    verificar_contrasena,
    generar_token,
    generar_contrasena_temporal,
    generar_token_restablecimiento,
)

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/registro", response_model=RegistroUsuarioOut)
def registrar_usuario(body: RegistroUsuarioIn, db: Session = Depends(get_db)):
    correo = body.correo.strip().lower()

    existe = db.query(Usuario).filter(Usuario.correo == correo).first()
    if existe:
        raise HTTPException(status_code=409, detail="El correo ya existe")

    contrasena_temporal = generar_contrasena_temporal(12)
    token = generar_token()

    usuario = Usuario(
        nombre=body.nombre.strip(),
        correo=correo,
        hash_contrasena=hashear_contrasena(contrasena_temporal),
        rol=(body.rol or "usuario").strip(),
        token=token,
        token_restablecer_contrasena=None,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return RegistroUsuarioOut(
        usuario_id=usuario.id,
        correo=usuario.correo,
        contrasena_temporal=None if IS_PROD else contrasena_temporal,
        token=usuario.token,
    )

@router.post("/login", response_model=LoginOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    correo = body.correo.strip().lower()
    usuario = db.query(Usuario).filter(Usuario.correo == correo).first()
    if not usuario or not verificar_contrasena(body.password, usuario.hash_contrasena):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return LoginOut(token=usuario.token)

@router.post("/restablecer/solicitud", response_model=ResetRequestOut)
def restablecer_solicitud(body: ResetRequestIn, db: Session = Depends(get_db)):
    correo = body.correo.strip().lower()
    usuario = db.query(Usuario).filter(Usuario.correo == correo).first()

    if not usuario:
        return ResetRequestOut(
            mensaje="Si el correo existe, se generó un token de restablecimiento.",
            token_restablecimiento="",
        )

    rt = generar_token_restablecimiento()
    usuario.token_restablecer_contrasena = rt
    db.commit()

    return ResetRequestOut(
        mensaje="Si el correo existe, se generó un token de restablecimiento.",
        token_restablecimiento="" if IS_PROD else rt,
    )

@router.post("/restablecer/confirmar", response_model=ResetConfirmOut)
def restablecer_confirmar(body: ResetConfirmIn, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(
        Usuario.token_restablecer_contrasena == body.token_restablecimiento
    ).first()
    if not usuario:
        raise HTTPException(status_code=400, detail="Token de restablecimiento inválido")

    usuario.hash_contrasena = hashear_contrasena(body.nueva_contrasena)
    usuario.token_restablecer_contrasena = None
    db.commit()
    return ResetConfirmOut(mensaje="Contraseña actualizada correctamente.")
