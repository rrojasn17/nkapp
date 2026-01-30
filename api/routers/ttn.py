from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple, List
import uuid
import logging
import json

from database import get_db
from config import TTN_WEBHOOK_SECRET
from models import Dispositivo, Dato, ValorDato

router = APIRouter(prefix="/ttn", tags=["TTN"])
logger = logging.getLogger("ttn")

def _safe_json(obj, limit: int = 4000) -> str:
    try:
        s = json.dumps(obj, ensure_ascii=False, default=str)
        return s[:limit] + ("…(truncado)" if len(s) > limit else "")
    except Exception:
        return str(obj)[:limit]

def extraer_eui(payload: Dict[str, Any]) -> Optional[str]:
    eui = (
        payload.get("end_device_ids", {}).get("dev_eui")
        or payload.get("end_device_ids", {}).get("device_id")
        or payload.get("devEUI")
        or payload.get("dev_eui")
        or payload.get("eui")
    )
    return eui.strip() if isinstance(eui, str) else None

def extraer_fecha_hora(payload: Dict[str, Any]) -> Optional[datetime]:
    ts = payload.get("received_at") or payload.get("time") or payload.get("timestamp")
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None
    return None

def elegir_payload(uplink_message: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    normalized = uplink_message.get("normalized_payload")
    if isinstance(normalized, dict) and normalized:
        data = normalized.get("data") if isinstance(normalized.get("data"), dict) else normalized
        if isinstance(data, dict) and data:
            return "normalized", data

    decoded = uplink_message.get("decoded_payload")
    if isinstance(decoded, dict) and decoded:
        return "decoded", decoded

    return "none", {}

def aplanar_numericos(obj: Any, prefijo: str = "") -> List[Tuple[str, float, Optional[str], str]]:
    salida: List[Tuple[str, float, Optional[str], str]] = []

    if isinstance(obj, dict):
        if "value" in obj and isinstance(obj["value"], (int, float)):
            unidad = obj.get("unit") if isinstance(obj.get("unit"), str) else None
            nombre = prefijo.split(".")[-1] if prefijo else "value"
            salida.append((nombre, float(obj["value"]), unidad, prefijo or nombre))
            return salida

        for k, v in obj.items():
            ruta = f"{prefijo}.{k}" if prefijo else str(k)
            salida.extend(aplanar_numericos(v, ruta))

    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            ruta = f"{prefijo}[{i}]"
            salida.extend(aplanar_numericos(v, ruta))

    elif isinstance(obj, (int, float)):
        nombre = prefijo.split(".")[-1] if prefijo else "value"
        salida.append((nombre, float(obj), None, prefijo or nombre))

    return salida

@router.post("/webhook")
async def ttn_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_webhook_secret: str = Header("", alias="X-Webhook-Secret"),
):
    rid = str(uuid.uuid4())[:8]

    if TTN_WEBHOOK_SECRET and x_webhook_secret != TTN_WEBHOOK_SECRET:
        logger.warning(f"[TTN][{rid}] 401 Unauthorized: X-Webhook-Secret inválido")
        raise HTTPException(status_code=401, detail="Webhook no autorizado")

    try:
        payload = await request.json()
    except Exception as e:
        logger.exception(f"[TTN][{rid}] 400 JSON inválido: {e}")
        raise HTTPException(status_code=400, detail="JSON inválido")

    eui = extraer_eui(payload) if isinstance(payload, dict) else None
    if not eui:
        logger.warning(f"[TTN][{rid}] sin eui/dev_eui. payload={_safe_json(payload)}")
        return {"status": "ok", "rid": rid, "note": "sin eui/dev_eui"}

    dispositivo = db.query(Dispositivo).filter(Dispositivo.eui == eui).first()
    if not dispositivo:
        logger.warning(f"[TTN][{rid}] dispositivo NO registrado. eui={eui}. payload={_safe_json(payload)}")
        return {"status": "ok", "rid": rid, "note": f"dispositivo no registrado eui={eui}"}

    uplink = payload.get("uplink_message") if isinstance(payload, dict) else {}
    uplink = uplink if isinstance(uplink, dict) else {}

    fecha_hora = extraer_fecha_hora(payload) or datetime.now(timezone.utc)
    origen, payload_elegido = elegir_payload(uplink)

    decoded_payload = uplink.get("decoded_payload")
    normalized_payload = uplink.get("normalized_payload")

    dato = Dato(
        dispositivo_id=dispositivo.id,
        fecha_hora=fecha_hora,
        origen=origen,
        json_crudo=payload,
        json_decodificado=decoded_payload if isinstance(decoded_payload, dict) else None,
        json_normalizado=normalized_payload if isinstance(normalized_payload, dict) else None,
    )
    db.add(dato)
    db.flush()

    items = aplanar_numericos(payload_elegido) if origen != "none" else []
    insertados = 0
    for nombre, valor, unidad, ruta in items:
        if valor != valor:
            continue
        db.add(ValorDato(
            dato_id=dato.id,
            nombre_variable=nombre,
            ruta_variable=ruta,
            unidad=unidad,
            valor=valor,
        ))
        insertados += 1

    db.commit()

    return {
        "status": "ok",
        "rid": rid,
        "eui": eui,
        "dispositivo_id": dispositivo.id,
        "dato_id": dato.id,
        "origen": origen,
        "insertados": insertados,
    }
