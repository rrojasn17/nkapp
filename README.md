# TTN Ingest + FastAPI + Postgres (Producción-ready)

Este proyecto recibe *uplinks* de **The Things Network / The Things Stack** y los almacena en PostgreSQL, con un modelo escalable basado en **mediciones** (una lectura por instante) y **valores** (variables infinitas por medición).

## Arquitectura de datos
- **usuarios** -> **unidades_productivas** -> **dispositivos** -> (**mediciones** -> **valores_medicion**)

### Enfoque recomendado: TTN `normalized_payload`
Configura TTN/TTS para que el webhook envíe `uplink_message.normalized_payload`. Así no hardcodeas decodificadores en el API: el API solo almacena lo que TTN normaliza.

---

# 1) Ejecutar en local (desarrollo)

## 1.1 Prerrequisitos
- Docker + Docker Compose

## 1.2 Arranque
1. Copia `.env.example` a `.env` y ajusta si lo deseas:
   
   ```bash
   cp .env.example .env
   ```

2. Levanta servicios:

   ```bash
   docker compose up -d --build
   ```

3. Verifica logs:

   ```bash
   docker compose logs -f api
   ```

## 1.3 Accesos
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- pgAdmin: `http://localhost:5050` (usuario `admin@local.com`, pass `admin`)

---

# 2) Flujo completo de pruebas con Postman

## 2.1 Registrar usuario
**POST** `http://localhost:8000/auth/registro`

Body JSON:
```json
{
  "nombre": "Reymond",
  "correo": "reymond@demo.com",
  "rol": "usuario"
}
```

Respuesta (en local devuelve contraseña temporal):
- `token`
- `contrasena_temporal`

## 2.2 Login
**POST** `http://localhost:8000/auth/login`

```json
{
  "correo": "reymond@demo.com",
  "password": "<contrasena_temporal>"
}
```

Guarda el `token` para las siguientes llamadas.

### Header estándar
En endpoints protegidos usa:
- `X-API-Token: <token>`

## 2.3 Crear unidad productiva
**POST** `http://localhost:8000/unidades-productivas`

Headers:
- `X-API-Token: <token>`

Body:
```json
{
  "nombre": "Finca 1",
  "area": 3.2,
  "descripcion": "Cafetales tecnificados",
  "tipo": "cafe",
  "categoria": "productor",
  "direccion": "Costa Rica",
  "georreferenciacion": "9.935,-84.091"
}
```

## 2.4 Crear dispositivo
**POST** `http://localhost:8000/dispositivos`

Headers:
- `X-API-Token: <token>`

Body:
```json
{
  "unidad_productiva_id": 1,
  "marca": "Dragino",
  "tipo": "soil",
  "identificador_dispositivo": "DS20L",
  "eui": "A84041FFFF123456"
}
```

## 2.5 Simular TTN webhook (normalized)
**POST** `http://localhost:8000/ttn/webhook`

Opcional si configuraste `TTN_WEBHOOK_SECRET` en `.env`:
- `X-Webhook-Secret: <TTN_WEBHOOK_SECRET>`

Body (ejemplo mínimo):
```json
{
  "raw": {
    "end_device_ids": {
      "dev_eui": "A84041FFFF123456"
    },
    "received_at": "2026-01-15T18:00:00Z",
    "uplink_message": {
      "normalized_payload": {
        "soil": {
          "ec": {"value": 1.23, "unit": "mS/cm"},
          "temperature": {"value": 24.8, "unit": "C"}
        },
        "air": {
          "humidity": {"value": 78.0, "unit": "%"}
        }
      }
    }
  }
}
```

## 2.6 Consultar datos (lista)
**GET** `http://localhost:8000/datos?eui=A84041FFFF123456&nombre_variable=ec&limite=200`

Headers:
- `X-API-Token: <token>`

También puedes filtrar por:
- `ruta_variable=soil.ec.value`
- `inicio=2026-01-15T00:00:00Z`
- `fin=2026-01-16T00:00:00Z`

## 2.7 Serie temporal para gráficos
**GET** `http://localhost:8000/dispositivos/1/series?ruta_variable=soil.ec.value&limite=5000`

Headers:
- `X-API-Token: <token>`

---

# 3) Ir a producción (Caddy + TLS)

## 3.1 Preparar DNS
Apunta tu subdominio (ej. `api-iotis.ruralcr.com`) hacia la IP del servidor.

## 3.2 Preparar archivos
1. Copia `.env.prod.example` a `.env.prod` y configura valores reales.
2. Edita `Caddyfile` y cambia `api.tudominio.com` por tu dominio real.

## 3.3 Levantar
En el servidor:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Verifica logs:
```bash
docker compose -f docker-compose.prod.yml logs -f caddy
```

---

# Notas de seguridad
- En `APP_ENV=prod`, el endpoint de registro **no devuelve** contraseña temporal.
- En producción deberías implementar entrega de contraseñas por correo o flujo de invitación.
- Para migraciones reales, se recomienda **Alembic**.
