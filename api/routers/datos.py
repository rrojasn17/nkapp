from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from database import get_db
from core.deps import get_current_user
from models import Dispositivo, Dato, ValorDato
from schemas import ConsultaDatosOut

router = APIRouter(tags=["Datos"])

@router.get("/datos", response_model=ConsultaDatosOut)
def obtener_datos(
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user),
    eui: Optional[str] = Query(None),
    ruta_variable: Optional[str] = Query(None),
    nombre_variable: Optional[str] = Query(None),
    inicio: Optional[datetime] = Query(None),
    fin: Optional[datetime] = Query(None),
    limite: int = Query(200, ge=1, le=2000),
):
    q = (
        db.query(ValorDato, Dato, Dispositivo)
        .join(Dato, ValorDato.dato_id == Dato.id)
        .join(Dispositivo, Dato.dispositivo_id == Dispositivo.id)
        .filter(Dispositivo.usuario_id == usuario.id)
    )

    if eui:
        q = q.filter(Dispositivo.eui == eui)
    if ruta_variable:
        q = q.filter(ValorDato.ruta_variable == ruta_variable)
    if nombre_variable:
        q = q.filter(ValorDato.nombre_variable == nombre_variable)
    if inicio:
        q = q.filter(Dato.fecha_hora >= inicio)
    if fin:
        q = q.filter(Dato.fecha_hora <= fin)

    rows = q.order_by(Dato.fecha_hora.desc()).limit(limite).all()

    items = []
    for valor_row, dato_row, disp in rows:
        items.append({
            "eui": disp.eui,
            "dispositivo_id": disp.id,
            "fecha_hora": dato_row.fecha_hora,
            "origen": dato_row.origen,
            "nombre_variable": valor_row.nombre_variable,
            "ruta_variable": valor_row.ruta_variable,
            "unidad": valor_row.unidad,
            "valor": float(valor_row.valor),
        })

    return {"items": items}

@router.get("/dispositivos/{dispositivo_id}/series")
def serie_dispositivo(
    dispositivo_id: int,
    ruta_variable: str = Query(...),
    inicio: Optional[datetime] = Query(None),
    fin: Optional[datetime] = Query(None),
    limite: int = Query(5000, ge=1, le=20000),
    db: Session = Depends(get_db),
    usuario = Depends(get_current_user),
):
    dispositivo = (
        db.query(Dispositivo)
        .filter(Dispositivo.id == dispositivo_id, Dispositivo.usuario_id == usuario.id)
        .first()
    )
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Dispositivo no existe o no pertenece al usuario")

    q = (
        db.query(Dato.fecha_hora, ValorDato.valor, ValorDato.unidad)
        .join(Dato, ValorDato.dato_id == Dato.id)
        .filter(Dato.dispositivo_id == dispositivo.id)
        .filter(ValorDato.ruta_variable == ruta_variable)
        .order_by(Dato.fecha_hora.desc())
    )

    if inicio:
        q = q.filter(Dato.fecha_hora >= inicio)
    if fin:
        q = q.filter(Dato.fecha_hora <= fin)

    rows = q.limit(limite).all()

    return {
        "dispositivo_id": dispositivo.id,
        "eui": dispositivo.eui,
        "ruta_variable": ruta_variable,
        "puntos": [{"t": r[0], "v": float(r[1]), "u": r[2]} for r in rows],
    }
