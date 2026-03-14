# Sistema de Gestión de Citas Médicas

API REST para gestionar médicos, pacientes y citas médicas, construida con FastAPI y SQLAlchemy.

## Arquitectura

```
Presentación (Routers FastAPI)
        ↓
Aplicación (Services)
        ↓
Dominio (Entities, Rules, Exceptions)
        ↓
Infraestructura (SQLAlchemy Models, Repositories)
```

Cada capa solo conoce a la capa inmediatamente inferior. La capa de dominio **no depende de ningún framework** y se puede testear de forma aislada.

### Capa de Dominio (`app/domain/`)

Es el corazón del sistema. Contiene la lógica de negocio pura, sin dependencias de frameworks ni bases de datos.

| Archivo | Responsabilidad |
|---|---|
| `enums.py` | Define los estados posibles de una cita (`PROGRAMADA`, `COMPLETADA`, `CANCELADA`, `REPROGRAMADA`) y las transiciones válidas entre ellos. |
| `entities.py` | Modela las entidades del negocio (`Doctor`, `Paciente`, `Cita`) como dataclasses puras de Python. |
| `exceptions.py` | Define excepciones específicas del dominio: `CitaSolapadaError`, `CitaEnPasadoError`, `EstadoCitaInvalidoError`, `DuplicadoError`, `EntidadNoEncontradaError`, `EmailInvalidoError`. |
| `rules.py` | Funciones puras que implementan las reglas de negocio: validar que no haya citas solapadas, que la fecha sea futura, que la transición de estado sea permitida y que el email tenga formato válido. |

### Capa de Infraestructura (`app/infrastructure/`)

Se encarga de la persistencia y el acceso a datos. Es la única capa que conoce SQLAlchemy y la base de datos.

| Archivo | Responsabilidad |
|---|---|
| `database.py` | Configura el engine de SQLAlchemy, la session factory (`SessionLocal`) y la clase base declarativa (`Base`). |
| `models.py` | Define los modelos SQLAlchemy que se mapean a las tablas de la base de datos (`DoctorModel`, `PacienteModel`, `CitaModel`) con sus relaciones, foreign keys y restricciones de unicidad. |
| `repositories/base.py` | Repositorio abstracto genérico con operaciones CRUD comunes (`get_by_id`, `get_all`, `create`, `update`, `delete`). |
| `repositories/doctor_repo.py` | Repositorio de doctores. Agrega búsqueda por número de licencia. |
| `repositories/paciente_repo.py` | Repositorio de pacientes. Agrega búsqueda por documento. |
| `repositories/cita_repo.py` | Repositorio de citas. Agrega consultas por doctor, por paciente, por rango de fechas y filtrado de citas activas. |

### Capa de Aplicación (`app/application/`)

Orquesta el flujo entre la capa de dominio y los repositorios. Aquí viven los casos de uso del sistema.

| Archivo | Responsabilidad |
|---|---|
| `schemas.py` | Define los DTOs (Data Transfer Objects) con Pydantic: los modelos de entrada (`DoctorCreate`, `CitaCreate`, etc.) y de salida (`DoctorResponse`, `CitaResponse`, `DisponibilidadResponse`). Incluye validación automática de email con `EmailStr`. |
| `doctor_service.py` | Casos de uso de doctores: registrar (con validación de licencia duplicada), obtener por ID y listar todos. |
| `paciente_service.py` | Casos de uso de pacientes: registrar (con validación de documento duplicado y email), obtener por ID y listar todos. |
| `cita_service.py` | Casos de uso de citas: agendar (validando fecha futura y solapamiento), cancelar (validando transición de estado), reprogramar (marca la original y crea una nueva), consultar disponibilidad (calcula slots libres en el horario laboral) y listar por doctor o paciente. |

### Capa de Presentación (`app/presentation/`)

Expone la funcionalidad como una API REST HTTP. Es la única capa que conoce FastAPI.

| Archivo | Responsabilidad |
|---|---|
| `dependencies.py` | Configura la inyección de dependencias de FastAPI: provee la sesión de base de datos (`get_db`) y las instancias de los servicios (`get_doctor_service`, `get_paciente_service`, `get_cita_service`). |
| `error_handlers.py` | Traduce las excepciones de dominio a respuestas HTTP con el código de estado apropiado (404, 409, 422). |
| `routers/doctor_router.py` | Endpoints REST para doctores (`POST`, `GET`, `GET/{id}`). |
| `routers/paciente_router.py` | Endpoints REST para pacientes (`POST`, `GET`, `GET/{id}`). |
| `routers/cita_router.py` | Endpoints REST para citas (agendar, cancelar, reprogramar, disponibilidad, listar por doctor/paciente). |

## Levantar el proyecto en local

### Requisitos previos

- **Python 3.11+** — verificar con `python3 --version`
- **pip** o **uv** como gestor de paquetes
- (Opcional) **pyenv** si necesitás manejar múltiples versiones de Python

### Paso 1 — Clonar y entrar al proyecto

```bash
cd ~/Documents/personal
git clone <url-del-repo> citas_medicas
cd citas_medicas
```

### Paso 2 — Crear el entorno virtual

Con `venv` (estándar):

```bash
python3 -m venv .venv
```

O con `uv` (más rápido):

```bash
uv venv --python 3.12 .venv
```

### Paso 3 — Activar el entorno virtual

```bash
source .venv/bin/activate
```

Deberías ver `(.venv)` al inicio de tu terminal.

### Paso 4 — Instalar dependencias

Con `pip`:

```bash
pip install -e ".[dev]"
```

O con `uv`:

```bash
uv pip install -e ".[dev]"
```

Esto instala tanto las dependencias del proyecto como las de desarrollo (pytest, httpx).

### Paso 5 — Aplicar migraciones de base de datos

```bash
alembic upgrade head
```

Esto crea el archivo `citas_medicas.db` (SQLite) con las tablas `doctores`, `pacientes` y `citas`.

### Paso 6 — Levantar el servidor

```bash
uvicorn app.main:app --reload
```

El servidor arranca en `http://localhost:8000` con hot-reload (se reinicia al guardar cambios).

### Paso 7 — Verificar que funciona

Abrir en el navegador:

- **Health check:** http://localhost:8000/health → debe devolver `{"status": "ok"}`
- **Swagger UI:** http://localhost:8000/docs → documentación interactiva donde podés probar todos los endpoints
- **ReDoc:** http://localhost:8000/redoc → documentación alternativa

O desde la terminal:

```bash
curl http://localhost:8000/health
```

### Paso 8 — Ejecutar los tests

```bash
pytest -v
```

Resultado esperado: **58 tests passed**.

### Resumen rápido (copiar y pegar)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

## Configuración

Variables de entorno (o archivo `.env`):

| Variable | Default | Descripción |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./citas_medicas.db` | URL de conexión a la base de datos |
| `DURACION_CITA_MINUTOS` | `30` | Duración estándar de cada cita |
| `HORARIO_INICIO` | `8` | Hora de inicio del horario laboral |
| `HORARIO_FIN` | `18` | Hora de fin del horario laboral |

### Cambiar a PostgreSQL

```bash
# Instalar driver
pip install psycopg2-binary

# Configurar variable de entorno
export DATABASE_URL="postgresql://usuario:password@localhost:5432/citas_medicas"
```

## Endpoints

### Doctores

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/doctores` | Registrar médico |
| GET | `/api/v1/doctores` | Listar médicos |
| GET | `/api/v1/doctores/{id}` | Obtener médico |

### Pacientes

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/pacientes` | Registrar paciente |
| GET | `/api/v1/pacientes` | Listar pacientes |
| GET | `/api/v1/pacientes/{id}` | Obtener paciente |

### Citas

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/citas` | Agendar cita |
| PATCH | `/api/v1/citas/{id}/cancelar` | Cancelar cita |
| PATCH | `/api/v1/citas/{id}/reprogramar` | Reprogramar cita |
| GET | `/api/v1/doctores/{id}/disponibilidad?fecha=YYYY-MM-DD` | Consultar disponibilidad |
| GET | `/api/v1/doctores/{id}/citas?activas=true` | Citas por médico |
| GET | `/api/v1/pacientes/{id}/citas?activas=true` | Citas por paciente |

## Levantar con Docker

### Opción 1 — Docker directamente

```bash
# Construir la imagen
docker build -t citas-medicas .

# Levantar el contenedor
docker run -d --name citas-medicas -p 8000:8000 citas-medicas

# Verificar
curl http://localhost:8000/health

# Ver logs
docker logs citas-medicas

# Detener
docker stop citas-medicas && docker rm citas-medicas
```

### Opción 2 — Docker Compose

```bash
docker compose up -d

# Detener
docker compose down
```

### Ejecutar tests dentro del contenedor

```bash
docker exec citas-medicas pytest -v
```

---

## Ejemplos de uso (Postman / curl)

La URL base es `http://localhost:8000`. Todos los ejemplos funcionan tanto con curl como importándolos en Postman.

### 1. Registrar un médico

```bash
curl -X POST http://localhost:8000/api/v1/doctores \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Dra. María López",
    "especialidad": "Cardiología",
    "numero_licencia": "MED-2026-001"
  }'
```

**Respuesta** (201):
```json
{
  "id": 1,
  "nombre": "Dra. María López",
  "especialidad": "Cardiología",
  "numero_licencia": "MED-2026-001"
}
```

### 2. Registrar un paciente

```bash
curl -X POST http://localhost:8000/api/v1/pacientes \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez",
    "documento": "DNI-40123456",
    "email": "juan.perez@email.com"
  }'
```

**Respuesta** (201):
```json
{
  "id": 1,
  "nombre": "Juan Pérez",
  "documento": "DNI-40123456",
  "email": "juan.perez@email.com"
}
```

### 3. Agendar una cita

```bash
curl -X POST http://localhost:8000/api/v1/citas \
  -H "Content-Type: application/json" \
  -d '{
    "paciente_id": 1,
    "doctor_id": 1,
    "fecha_hora": "2026-03-20T10:00:00"
  }'
```

**Respuesta** (201):
```json
{
  "id": 1,
  "paciente_id": 1,
  "doctor_id": 1,
  "fecha_hora": "2026-03-20T10:00:00",
  "duracion_minutos": 30,
  "estado": "PROGRAMADA"
}
```

### 4. Intentar agendar en el mismo horario (error de solapamiento)

```bash
curl -X POST http://localhost:8000/api/v1/citas \
  -H "Content-Type: application/json" \
  -d '{
    "paciente_id": 1,
    "doctor_id": 1,
    "fecha_hora": "2026-03-20T10:00:00"
  }'
```

**Respuesta** (409):
```json
{
  "detail": "El médico ya tiene una cita entre 10:00 y 10:30."
}
```

### 5. Consultar disponibilidad de un médico

```bash
curl http://localhost:8000/api/v1/doctores/1/disponibilidad?fecha=2026-03-20
```

**Respuesta** (200):
```json
{
  "doctor_id": 1,
  "fecha": "2026-03-20",
  "slots_disponibles": [
    {"hora_inicio": "08:00:00", "hora_fin": "08:30:00"},
    {"hora_inicio": "08:30:00", "hora_fin": "09:00:00"},
    {"hora_inicio": "09:00:00", "hora_fin": "09:30:00"},
    {"hora_inicio": "09:30:00", "hora_fin": "10:00:00"},
    {"hora_inicio": "10:30:00", "hora_fin": "11:00:00"},
    "... más slots ..."
  ]
}
```

El slot de 10:00 a 10:30 no aparece porque está ocupado.

### 6. Cancelar una cita

```bash
curl -X PATCH http://localhost:8000/api/v1/citas/1/cancelar
```

**Respuesta** (200):
```json
{
  "id": 1,
  "paciente_id": 1,
  "doctor_id": 1,
  "fecha_hora": "2026-03-20T10:00:00",
  "duracion_minutos": 30,
  "estado": "CANCELADA"
}
```

### 7. Reprogramar una cita

Primero agendar una nueva cita, luego reprogramarla:

```bash
curl -X PATCH http://localhost:8000/api/v1/citas/2/reprogramar \
  -H "Content-Type: application/json" \
  -d '{
    "nueva_fecha_hora": "2026-03-22T14:00:00"
  }'
```

**Respuesta** (200): devuelve la nueva cita creada con estado `PROGRAMADA`.

### 8. Listar citas de un médico (solo activas)

```bash
curl http://localhost:8000/api/v1/doctores/1/citas?activas=true
```

### 9. Listar citas de un paciente

```bash
curl http://localhost:8000/api/v1/pacientes/1/citas
```

### 10. Listar todos los médicos

```bash
curl http://localhost:8000/api/v1/doctores
```

### 11. Listar todos los pacientes

```bash
curl http://localhost:8000/api/v1/pacientes
```

---

### Importar en Postman

1. Abrir Postman → **Import** → **Raw text**
2. Pegar cualquiera de los curl de arriba
3. Postman lo convierte automáticamente a una request lista para usar
4. Alternativamente, apuntar Postman a `http://localhost:8000/openapi.json` para importar toda la colección desde el esquema OpenAPI

---

## Tests

```bash
pytest -v
```

## Migraciones (Alembic)

```bash
# Generar nueva migración
alembic revision --autogenerate -m "descripcion_del_cambio"

# Aplicar migraciones
alembic upgrade head

# Ver historial
alembic history
```
