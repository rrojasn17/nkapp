from fastapi import FastAPI, Depends, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Any, Dict, Tuple, List
import logging
import json
import uuid
from datetime import timezone

from database import Base, engine, get_db
from config import CORS_ORIGINS, IS_PROD, TTN_WEBHOOK_SECRET

from models import (
    Usuario,
    UnidadProductiva,
    Dispositivo,
    Medicion,
    ValorMedicion,
)

from schemas import (
    TTNWebhookIn,
    # Auth
    RegistroUsuarioIn, RegistroUsuarioOut,
    LoginIn, LoginOut,
    ResetRequestIn, ResetRequestOut,
    ResetConfirmIn, ResetConfirmOut,
    # Unidades productivas
    UnidadProductivaCreateIn, UnidadProductivaOut,
    # Dispositivos
    DispositivoCreateIn, DispositivoOut,
    # Datos
    ConsultaDatosOut,
)

from security import (
    hashear_contrasena,
    verificar_contrasena,
    generar_token,
    generar_contrasena_temporal,
    generar_token_restablecimiento,
)


app = FastAPI(title="Ingesta TTN + API (Producción-ready)")
logger = logging.getLogger("ttn")
logging.basicConfig(level=logging.INFO)

def _safe_json(obj, limit: int = 4000) -> str:
    try:
        s = json.dumps(obj, ensure_ascii=False, default=str)
        return s[:limit] + ("…(truncado)" if len(s) > limit else "")
    except Exception:
        return str(obj)[:limit]


# CORS configurable por variables de entorno
if CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Nota: en producción real se recomienda Alembic; esto es MVP
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


# =========================================================
# Helpers Auth
# =========================================================
def requerir_usuario_por_token(db: Session, token: str) -> Usuario:
    usuario = db.query(Usuario).filter(Usuario.token == token).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Token inválido")
    return usuario


# =========================================================
# AUTH
# =========================================================
@app.post("/auth/registro", response_model=RegistroUsuarioOut)
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

    # Producción: NO devolver contraseña temporal
    return RegistroUsuarioOut(
        usuario_id=usuario.id,
        correo=usuario.correo,
        contrasena_temporal=None if IS_PROD else contrasena_temporal,
        token=usuario.token,
    )


@app.post("/auth/login", response_model=LoginOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    correo = body.correo.strip().lower()
    usuario = db.query(Usuario).filter(Usuario.correo == correo).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    if not verificar_contrasena(body.password, usuario.hash_contrasena):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")

    return LoginOut(token=usuario.token)


@app.post("/auth/restablecer/solicitud", response_model=ResetRequestOut)
def restablecer_solicitud(body: ResetRequestIn, db: Session = Depends(get_db)):
    correo = body.correo.strip().lower()
    usuario = db.query(Usuario).filter(Usuario.correo == correo).first()

    # No revelar existencia
    if not usuario:
        return ResetRequestOut(
            mensaje="Si el correo existe, se generó un token de restablecimiento.",
            token_restablecimiento="",
        )

    rt = generar_token_restablecimiento()
    usuario.token_restablecer_contrasena = rt
    db.commit()

    # Producción: no devolver token
    return ResetRequestOut(
        mensaje="Si el correo existe, se generó un token de restablecimiento.",
        token_restablecimiento="" if IS_PROD else rt,
    )


@app.post("/auth/restablecer/confirmar", response_model=ResetConfirmOut)
def restablecer_confirmar(body: ResetConfirmIn, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.token_restablecer_contrasena == body.token_restablecimiento).first()
    if not usuario:
        raise HTTPException(status_code=400, detail="Token de restablecimiento inválido")

    usuario.hash_contrasena = hashear_contrasena(body.nueva_contrasena)
    usuario.token_restablecer_contrasena = None
    db.commit()
    return ResetConfirmOut(mensaje="Contraseña actualizada correctamente.")


# =========================================================
# Unidades productivas
# =========================================================
@app.post("/unidades-productivas", response_model=UnidadProductivaOut)
def crear_unidad_productiva(
    body: UnidadProductivaCreateIn,
    db: Session = Depends(get_db),
    x_api_token: str = Header(..., alias="X-API-Token"),
):
    usuario = requerir_usuario_por_token(db, x_api_token)

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


@app.get("/unidades-productivas", response_model=List[UnidadProductivaOut])
def listar_unidades_productivas(
    db: Session = Depends(get_db),
    x_api_token: str = Header(..., alias="X-API-Token"),
):
    usuario = requerir_usuario_por_token(db, x_api_token)
    return (
        db.query(UnidadProductiva)
        .filter(UnidadProductiva.usuario_id == usuario.id)
        .order_by(UnidadProductiva.id.desc())
        .all()
    )


# =========================================================
# Dispositivos
# =========================================================
@app.post("/dispositivos", response_model=DispositivoOut)
def crear_dispositivo(
    body: DispositivoCreateIn,
    db: Session = Depends(get_db),
    x_api_token: str = Header(..., alias="X-API-Token"),
):
    usuario = requerir_usuario_por_token(db, x_api_token)

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


@app.get("/dispositivos", response_model=List[DispositivoOut])
def listar_dispositivos(
    db: Session = Depends(get_db),
    x_api_token: str = Header(..., alias="X-API-Token"),
):
    usuario = requerir_usuario_por_token(db, x_api_token)
    return (
        db.query(Dispositivo)
        .filter(Dispositivo.usuario_id == usuario.id)
        .order_by(Dispositivo.id.desc())
        .all()
    )


# =========================================================
# Helpers TTN / TTS (normalized-first)
# =========================================================
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
    """Retorna (origen, payload): normalized > decoded."""
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
    """Convierte JSON arbitrario a lista de (nombre_variable, valor, unidad, ruta_variable)."""
    salida: List[Tuple[str, float, Optional[str], str]] = []

    if isinstance(obj, dict):
        # patrón normalized típico: {value: <num>, unit: "..."}
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


# =========================================================
# Webhook TTN/TTS -> Medicion + ValorMedicion
# =========================================================
@app.post("/ttn/webhook")
async def ttn_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_webhook_secret: str = Header("", alias="X-Webhook-Secret"),
):
    # ID corto para rastrear en logs
    rid = str(uuid.uuid4())[:8]

    # --- Seguridad ---
    if TTN_WEBHOOK_SECRET and x_webhook_secret != TTN_WEBHOOK_SECRET:
        logger.warning(f"[TTN][{rid}] 401 Unauthorized: X-Webhook-Secret inválido")
        raise HTTPException(status_code=401, detail="Webhook no autorizado")

    # --- Leer JSON crudo ---
    try:
        payload = await request.json()
    except Exception as e:
        logger.exception(f"[TTN][{rid}] 400 JSON inválido: {e}")
        raise HTTPException(status_code=400, detail="JSON inválido")

    # --- Logs base (para ver exactamente qué llega) ---
    headers = dict(request.headers)
    logger.info(f"[TTN][{rid}] IN content-type={headers.get('content-type')} user-agent={headers.get('user-agent')}")
    if isinstance(payload, dict):
        logger.info(f"[TTN][{rid}] IN top_keys={list(payload.keys())}")
    else:
        logger.warning(f"[TTN][{rid}] payload no es dict. type={type(payload)} body={_safe_json(payload)}")
        return {"status": "ok", "rid": rid, "note": "payload no es objeto JSON"}

    # Datos típicos TTN
    device_id = payload.get("end_device_ids", {}).get("device_id")
    dev_eui = payload.get("end_device_ids", {}).get("dev_eui")
    received_at = payload.get("received_at")
    logger.info(f"[TTN][{rid}] device_id={device_id} dev_eui={dev_eui} received_at={received_at}")

    # --- Resolver EUI ---
    eui = extraer_eui(payload)
    if not eui:
        # Guardar raw sería ideal, pero sin eui no podemos asociar a Dispositivo.
        logger.warning(f"[TTN][{rid}] sin eui/dev_eui. payload={_safe_json(payload)}")
        # Responder 200 para que TTN no reintente en bucle
        return {"status": "ok", "rid": rid, "note": "sin eui/dev_eui"}

    # --- Buscar dispositivo en BD ---
    dispositivo = db.query(Dispositivo).filter(Dispositivo.eui == eui).first()
    if not dispositivo:
        logger.warning(f"[TTN][{rid}] dispositivo NO registrado. eui={eui}. payload={_safe_json(payload)}")
        # Responder 200 para evitar reintentos; así podés ver el payload y registrar el dispositivo luego.
        return {"status": "ok", "rid": rid, "note": f"dispositivo no registrado eui={eui}"}

    # --- Uplink ---
    uplink = payload.get("uplink_message")
    uplink = uplink if isinstance(uplink, dict) else {}

    # --- Fecha/hora ---
    fecha_hora = extraer_fecha_hora(payload) or datetime.now(timezone.utc)

    # --- Elegir normalized/decoded ---
    origen, payload_elegido = elegir_payload(uplink)
    logger.info(f"[TTN][{rid}] origen={origen}")

    decoded_keys = None
    decoded_payload = uplink.get("decoded_payload")
    if isinstance(decoded_payload, dict):
        decoded_keys = list(decoded_payload.keys())
    logger.info(f"[TTN][{rid}] decoded_keys={decoded_keys}")

    # --- Guardar medición SIEMPRE (aunque no haya numéricos) ---
    medicion = Medicion(
        dispositivo_id=dispositivo.id,
        fecha_hora=fecha_hora,
        origen=origen,
        json_crudo=payload,
        json_decodificado=decoded_payload if isinstance(decoded_payload, dict) else None,
        json_normalizado=uplink.get("normalized_payload") if isinstance(uplink.get("normalized_payload"), dict) else None,
    )

    db.add(medicion)
    db.flush()  # obtener medicion.id

    # --- Aplanar numéricos ---
    items = aplanar_numericos(payload_elegido) if origen != "none" else []
    logger.info(f"[TTN][{rid}] numericos_encontrados={len(items)}")

    insertados = 0
    for nombre, valor, unidad, ruta in items:
        # filtrar NaN
        if valor != valor:
            continue
        db.add(
            ValorMedicion(
                medicion_id=medicion.id,
                nombre_variable=nombre,
                ruta_variable=ruta,
                unidad=unidad,
                valor=valor,
            )
        )
        insertados += 1

    db.commit()

    logger.info(f"[TTN][{rid}] OK medicion_id={medicion.id} insertados={insertados}")

    return {
        "status": "ok",
        "rid": rid,
        "eui": eui,
        "dispositivo_id": dispositivo.id,
        "medicion_id": medicion.id,
        "origen": origen,
        "insertados": insertados,
    }


# =========================================================
# Consulta dinámica de datos
# =========================================================
@app.get("/datos", response_model=ConsultaDatosOut)
def obtener_datos(
    db: Session = Depends(get_db),
    x_api_token: str = Header(..., alias="X-API-Token"),
    eui: Optional[str] = Query(None),
    ruta_variable: Optional[str] = Query(None),
    nombre_variable: Optional[str] = Query(None),
    inicio: Optional[datetime] = Query(None),
    fin: Optional[datetime] = Query(None),
    limite: int = Query(200, ge=1, le=2000),
):
    usuario = requerir_usuario_por_token(db, x_api_token)

    q = (
        db.query(ValorMedicion, Medicion, Dispositivo)
        .join(Medicion, ValorMedicion.medicion_id == Medicion.id)
        .join(Dispositivo, Medicion.dispositivo_id == Dispositivo.id)
        .filter(Dispositivo.usuario_id == usuario.id)
    )

    if eui:
        q = q.filter(Dispositivo.eui == eui)
    if ruta_variable:
        q = q.filter(ValorMedicion.ruta_variable == ruta_variable)
    if nombre_variable:
        q = q.filter(ValorMedicion.nombre_variable == nombre_variable)
    if inicio:
        q = q.filter(Medicion.fecha_hora >= inicio)
    if fin:
        q = q.filter(Medicion.fecha_hora <= fin)

    rows = q.order_by(Medicion.fecha_hora.desc()).limit(limite).all()

    items = []
    for valor_med, med, disp in rows:
        items.append(
            {
                "eui": disp.eui,
                "dispositivo_id": disp.id,
                "fecha_hora": med.fecha_hora,
                "origen": med.origen,
                "nombre_variable": valor_med.nombre_variable,
                "ruta_variable": valor_med.ruta_variable,
                "unidad": valor_med.unidad,
                "valor": float(valor_med.valor),
            }
        )

    return {"items": items}


# =========================================================
# Serie temporal (gráficos)
# =========================================================
@app.get("/dispositivos/{dispositivo_id}/series")
def serie_dispositivo(
    dispositivo_id: int,
    ruta_variable: str = Query(...),
    inicio: Optional[datetime] = Query(None),
    fin: Optional[datetime] = Query(None),
    limite: int = Query(5000, ge=1, le=20000),
    db: Session = Depends(get_db),
    x_api_token: str = Header(..., alias="X-API-Token"),
):
    usuario = requerir_usuario_por_token(db, x_api_token)

    dispositivo = (
        db.query(Dispositivo)
        .filter(Dispositivo.id == dispositivo_id, Dispositivo.usuario_id == usuario.id)
        .first()
    )
    if not dispositivo:
        raise HTTPException(status_code=404, detail="Dispositivo no existe o no pertenece al usuario")

    q = (
        db.query(Medicion.fecha_hora, ValorMedicion.valor, ValorMedicion.unidad)
        .join(Medicion, ValorMedicion.medicion_id == Medicion.id)
        .filter(Medicion.dispositivo_id == dispositivo.id)
        .filter(ValorMedicion.ruta_variable == ruta_variable)
        .order_by(Medicion.fecha_hora.desc())
    )

    if inicio:
        q = q.filter(Medicion.fecha_hora >= inicio)
    if fin:
        q = q.filter(Medicion.fecha_hora <= fin)

    rows = q.limit(limite).all()

    return {
        "dispositivo_id": dispositivo.id,
        "eui": dispositivo.eui,
        "ruta_variable": ruta_variable,
        "puntos": [{"t": r[0], "v": float(r[1]), "u": r[2]} for r in rows],
    }
