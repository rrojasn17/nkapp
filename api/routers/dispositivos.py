from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from core.deps import get_current_user
from models import Dispositivo, UnidadProductiva
from schemas import DispositivoCreateIn, DispositivoOut

router = APIRouter(prefix="/dispositivos", tags=["Dispositivos"])

@router.post("", response_model=DispositivoOut)
def crear_dispositivo(
    body: DispositivoCreateIn,
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user),
):
    unidad = db.query(UnidadProductiva).filter(
        UnidadProductiva.id == body.unidad_productiva_id,
        UnidadProductiva.usuario_id == usuario.id,
    ).first()
    if not unidad:
        raise HTTPException(status_code=404, detail="Unidad productiva no existe o no pertenece al usuario")

    eui = body.eui.strip()
    existe = db.query(Dispositivo).filter(Dispositivo.eui == eui).first()
    if existe:
        raise HTTPException(status_code=409, detail="Ese EUI ya está registrado")

    dispositivo = Dispositivo(
        usuario_id=usuario.id,
        unidad_productiva_id=unidad.id,
        marca=body.marca,
        identificador_dispositivo=body.identificador_dispositivo,
        tipo=body.tipo,
        eui=eui,
    )
    db.add(dispositivo)
    db.commit()
    db.refresh(dispositivo)
    return dispositivo

@router.get("", response_model=List[DispositivoOut])
def listar_dispositivos(
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user),
):
    return (
        db.query(Dispositivo)
        .filter(Dispositivo.usuario_id == usuario.id)
        .order_by(Dispositivo.id.desc())
        .all()
    )
