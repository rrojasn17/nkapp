from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from core.deps import get_current_user
from models import UnidadProductiva
from schemas import UnidadProductivaCreateIn, UnidadProductivaOut

router = APIRouter(prefix="/unidades-productivas", tags=["Unidades productivas"])

@router.post("", response_model=UnidadProductivaOut)
def crear_unidad_productiva(
    body: UnidadProductivaCreateIn,
    db: Session = Depends(get_db),              # ✅ así
    usuario = Depends(get_current_user),        # ✅ así
):
    unidad = UnidadProductiva(
        usuario_id=usuario.id,
        nombre=body.nombre.strip(),
        area=body.area,
        descripcion=body.descripcion,
        cualidades=body.cualidades,
        tipo=body.tipo,
        categoria=body.categoria,
        direccion=body.direccion,
        georreferenciacion=body.georreferenciacion,
    )
    db.add(unidad)
    db.commit()
    db.refresh(unidad)
    return unidad

@router.get("", response_model=List[UnidadProductivaOut])
def listar_unidades_productivas(
    db: Session = Depends(get_db),              # ✅ así
    usuario = Depends(get_current_user),        # ✅ así
):
    return (
        db.query(UnidadProductiva)
        .filter(UnidadProductiva.usuario_id == usuario.id)
        .order_by(UnidadProductiva.id.desc())
        .all()
    )
