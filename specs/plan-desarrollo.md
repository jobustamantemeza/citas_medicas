# Plan de Desarrollo — Sistema de Gestión de Citas Médicas

> Basado en: `specs/spec-1.md`

---

## Análisis Previo

### Alcance del sistema
Sistema backend REST en Python para gestionar médicos, pacientes y citas médicas, con reglas de negocio que impiden inconsistencias (solapamiento de horarios, citas en el pasado, etc.).

### Stack tecnológico
| Componente     | Tecnología                |
|----------------|---------------------------|
| Framework API  | FastAPI                   |
| ORM            | SQLAlchemy (async o sync) |
| Base de datos  | SQLite (default) / PostgreSQL (configurable) |
| Validación     | Pydantic v2               |
| Testing        | pytest + httpx (TestClient) |
| Migraciones    | Alembic                   |

### Arquitectura objetivo
```
Presentación (API / Routers)
        ↓
Aplicación (Services / Use Cases)
        ↓
Dominio (Entities, Value Objects, Business Rules, Exceptions)
        ↓
Repositorio (SQLAlchemy Models, Repository implementations)
```

Cada capa solo conoce a la capa inmediatamente inferior. La capa de dominio **no depende de infraestructura**.

### Entidades identificadas
| Entidad      | Campos clave                                          | Restricciones          |
|--------------|-------------------------------------------------------|------------------------|
| **Doctor**   | id, nombre, especialidad, número de licencia          | licencia única         |
| **Paciente** | id, nombre, documento, correo electrónico             | documento único, email válido |
| **Cita**     | id, paciente_id, doctor_id, fecha_hora, estado, duración | sin solapamiento, no en pasado |

### Estados de una cita
```
PROGRAMADA → COMPLETADA
PROGRAMADA → CANCELADA
PROGRAMADA → REPROGRAMADA → (nueva cita PROGRAMADA)
```

---

## Estructura de Carpetas Propuesta

```
citas_medicas/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Entry point FastAPI
│   ├── config.py                  # Settings (duración cita, DB URL, etc.)
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities.py            # Doctor, Paciente, Cita (dataclasses / Pydantic base)
│   │   ├── enums.py               # EstadoCita enum
│   │   ├── exceptions.py          # Excepciones de dominio
│   │   └── rules.py               # Reglas de negocio puras
│   ├── application/
│   │   ├── __init__.py
│   │   ├── schemas.py             # DTOs Pydantic (request/response)
│   │   ├── doctor_service.py
│   │   ├── paciente_service.py
│   │   └── cita_service.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── database.py            # Engine, SessionLocal, Base
│   │   ├── models.py              # Modelos SQLAlchemy (tablas)
│   │   └── repositories/
│   │       ├── __init__.py
│   │       ├── base.py            # Repositorio abstracto
│   │       ├── doctor_repo.py
│   │       ├── paciente_repo.py
│   │       └── cita_repo.py
│   └── presentation/
│       ├── __init__.py
│       ├── dependencies.py        # Dependency injection (get_db, get_services)
│       ├── error_handlers.py      # Mapeo excepciones dominio → HTTP
│       └── routers/
│           ├── __init__.py
│           ├── doctor_router.py
│           ├── paciente_router.py
│           └── cita_router.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Fixtures (DB en memoria, client)
│   ├── unit/
│   │   ├── test_rules.py          # Reglas de negocio
│   │   ├── test_doctor_service.py
│   │   ├── test_paciente_service.py
│   │   └── test_cita_service.py
│   └── integration/
│       ├── test_doctor_api.py
│       ├── test_paciente_api.py
│       └── test_cita_api.py
├── alembic/                       # Migraciones
│   └── ...
├── alembic.ini
├── pyproject.toml                 # o requirements.txt
└── README.md
```

---

## FASE 1 — Inicialización del proyecto y configuración

**Objetivo:** Tener el esqueleto del proyecto funcionando con FastAPI levantando un health-check y la base de datos conectada.

### Pasos

1.1. Crear estructura de carpetas y archivos `__init__.py`.

1.2. Crear `pyproject.toml` (o `requirements.txt`) con dependencias:
   - `fastapi`
   - `uvicorn[standard]`
   - `sqlalchemy`
   - `pydantic[email]` (para validar emails)
   - `pydantic-settings` (para configuración)
   - `alembic`
   - `pytest`, `httpx` (dev)

1.3. Crear `app/config.py`:
   - `DATABASE_URL` (default SQLite, documentar cambio a PostgreSQL)
   - `DURACION_CITA_MINUTOS` (default 30, configurable por env var)

1.4. Crear `app/infrastructure/database.py`:
   - Engine SQLAlchemy
   - `SessionLocal` factory
   - `Base` declarativa
   - Función `create_tables()` para desarrollo

1.5. Crear `app/main.py`:
   - Instancia FastAPI
   - Evento `lifespan` para crear tablas al iniciar
   - Endpoint `GET /health` que retorne `{"status": "ok"}`

1.6. Verificar que `uvicorn app.main:app --reload` levanta sin errores.

### Entregable
- Proyecto que arranca, responde en `/health` y crea la base SQLite vacía.

---

## FASE 2 — Capa de Dominio

**Objetivo:** Definir las entidades, enumeraciones, excepciones y reglas de negocio **sin dependencia de infraestructura**.

### Pasos

2.1. Crear `app/domain/enums.py`:
   - `EstadoCita` con valores: `PROGRAMADA`, `COMPLETADA`, `CANCELADA`, `REPROGRAMADA`

2.2. Crear `app/domain/entities.py` (dataclasses puras):
   - `Doctor(id, nombre, especialidad, numero_licencia)`
   - `Paciente(id, nombre, documento, email)`
   - `Cita(id, paciente_id, doctor_id, fecha_hora, duracion_minutos, estado)`

2.3. Crear `app/domain/exceptions.py`:
   - `CitaSolapadaError` — el médico ya tiene cita en ese horario
   - `CitaEnPasadoError` — la fecha es anterior a ahora
   - `EstadoCitaInvalidoError` — transición de estado no permitida
   - `EmailInvalidoError`
   - `EntidadNoEncontradaError` — doctor/paciente/cita no existe
   - `DuplicadoError` — licencia o documento ya registrado

2.4. Crear `app/domain/rules.py` — funciones puras que validan:
   - `validar_no_solapamiento(citas_existentes, nueva_fecha, duracion)` → lanza `CitaSolapadaError`
   - `validar_fecha_futura(fecha)` → lanza `CitaEnPasadoError`
   - `validar_transicion_estado(estado_actual, nuevo_estado)` → lanza `EstadoCitaInvalidoError`
   - `validar_email(email)` → lanza `EmailInvalidoError`
   - `calcular_fin_cita(inicio, duracion_minutos)` → devuelve datetime

### Entregable
- Módulo de dominio 100% independiente, sin imports de SQLAlchemy ni FastAPI.
- Se puede testear aisladamente.

---

## FASE 3 — Capa de Repositorio (Infraestructura / Datos)

**Objetivo:** Implementar la persistencia con SQLAlchemy y exponer interfaces de repositorio.

### Pasos

3.1. Crear `app/infrastructure/models.py` — modelos SQLAlchemy:
   - `DoctorModel` (tabla `doctores`)
     - `id` (PK, autoincrement)
     - `nombre` (String, not null)
     - `especialidad` (String, not null)
     - `numero_licencia` (String, unique, not null)
   - `PacienteModel` (tabla `pacientes`)
     - `id` (PK)
     - `nombre` (String, not null)
     - `documento` (String, unique, not null)
     - `email` (String, not null)
   - `CitaModel` (tabla `citas`)
     - `id` (PK)
     - `paciente_id` (FK → pacientes.id)
     - `doctor_id` (FK → doctores.id)
     - `fecha_hora` (DateTime, not null)
     - `duracion_minutos` (Integer, not null)
     - `estado` (String/Enum, not null, default PROGRAMADA)
     - Relaciones: `doctor`, `paciente`

3.2. Crear `app/infrastructure/repositories/base.py`:
   - Clase abstracta `BaseRepository` con métodos genéricos: `get_by_id`, `get_all`, `create`, `update`, `delete`

3.3. Crear `app/infrastructure/repositories/doctor_repo.py`:
   - `DoctorRepository(BaseRepository)`
   - Métodos adicionales: `get_by_licencia(numero_licencia)`

3.4. Crear `app/infrastructure/repositories/paciente_repo.py`:
   - `PacienteRepository(BaseRepository)`
   - Métodos adicionales: `get_by_documento(documento)`

3.5. Crear `app/infrastructure/repositories/cita_repo.py`:
   - `CitaRepository(BaseRepository)`
   - Métodos adicionales:
     - `get_by_doctor(doctor_id, solo_activas=False)`
     - `get_by_paciente(paciente_id, solo_activas=False)`
     - `get_citas_doctor_en_rango(doctor_id, inicio, fin)` — para validar solapamiento

3.6. Configurar Alembic para migraciones:
   - `alembic init alembic`
   - Apuntar `env.py` al `Base.metadata` y `DATABASE_URL` del config
   - Generar migración inicial

### Entregable
- Modelos mapeados, repositorios funcionales, migración inicial generada.
- La base de datos se crea correctamente con todas las tablas y restricciones.

---

## FASE 4 — Capa de Aplicación (Servicios)

**Objetivo:** Implementar la lógica de orquestación que conecta dominio con repositorios.

### Pasos

4.1. Crear `app/application/schemas.py` — DTOs Pydantic:
   - **Doctor:**
     - `DoctorCreate(nombre, especialidad, numero_licencia)`
     - `DoctorResponse(id, nombre, especialidad, numero_licencia)` con `model_config = ConfigDict(from_attributes=True)`
   - **Paciente:**
     - `PacienteCreate(nombre, documento, email)` — con `EmailStr` para validar formato
     - `PacienteResponse(id, nombre, documento, email)`
   - **Cita:**
     - `CitaCreate(paciente_id, doctor_id, fecha_hora)`
     - `CitaReprogramar(nueva_fecha_hora)`
     - `CitaResponse(id, paciente_id, doctor_id, fecha_hora, duracion_minutos, estado)`
   - **Disponibilidad:**
     - `DisponibilidadResponse(doctor_id, fecha, horarios_disponibles: list[time])`

4.2. Crear `app/application/doctor_service.py`:
   - `registrar_doctor(data)`:
     1. Verificar que `numero_licencia` no exista → `DuplicadoError`
     2. Crear y retornar

   - `obtener_doctor(id)`: buscar o lanzar `EntidadNoEncontradaError`
   - `listar_doctores()`: retornar todos

4.3. Crear `app/application/paciente_service.py`:
   - `registrar_paciente(data)`:
     1. Validar email (regla de dominio)
     2. Verificar que `documento` no exista → `DuplicadoError`
     3. Crear y retornar

   - `obtener_paciente(id)`: buscar o lanzar `EntidadNoEncontradaError`
   - `listar_pacientes()`: retornar todos

4.4. Crear `app/application/cita_service.py`:
   - `agendar_cita(data)`:
     1. Validar que el doctor existe
     2. Validar que el paciente existe
     3. `validar_fecha_futura(fecha_hora)`
     4. Obtener citas del doctor en el rango `[fecha_hora, fecha_hora + duración]`
     5. `validar_no_solapamiento(citas, fecha_hora, duración)`
     6. Crear cita con estado `PROGRAMADA`

   - `cancelar_cita(cita_id)`:
     1. Obtener cita o `EntidadNoEncontradaError`
     2. `validar_transicion_estado(actual, CANCELADA)`
     3. Actualizar estado

   - `reprogramar_cita(cita_id, nueva_fecha)`:
     1. Obtener cita original
     2. `validar_transicion_estado(actual, REPROGRAMADA)`
     3. `validar_fecha_futura(nueva_fecha)`
     4. Verificar no solapamiento en nueva fecha
     5. Marcar cita original como `REPROGRAMADA`
     6. Crear nueva cita con estado `PROGRAMADA`
     7. Retornar nueva cita

   - `consultar_disponibilidad(doctor_id, fecha)`:
     1. Obtener citas activas del doctor en esa fecha
     2. Calcular slots libres en horario laboral (ej: 08:00-18:00)
     3. Retornar lista de horarios disponibles

   - `listar_citas_por_doctor(doctor_id, solo_activas)`
   - `listar_citas_por_paciente(paciente_id, solo_activas)`

### Entregable
- Servicios que orquestan repositorios + reglas de dominio.
- Ningún servicio accede directamente a SQLAlchemy: solo usa repositorios.

---

## FASE 5 — Capa de Presentación (API REST)

**Objetivo:** Exponer la funcionalidad como endpoints HTTP con manejo de errores apropiado.

### Pasos

5.1. Crear `app/presentation/dependencies.py`:
   - `get_db()` — yield session con manejo de commit/rollback
   - `get_doctor_service(db)`, `get_paciente_service(db)`, `get_cita_service(db)`

5.2. Crear `app/presentation/error_handlers.py`:
   - Mapear excepciones de dominio a códigos HTTP:
     - `EntidadNoEncontradaError` → 404
     - `DuplicadoError` → 409
     - `CitaSolapadaError` → 409
     - `CitaEnPasadoError` → 422
     - `EstadoCitaInvalidoError` → 422
     - `EmailInvalidoError` → 422

5.3. Crear `app/presentation/routers/doctor_router.py`:
   - `POST /api/v1/doctores` — registrar doctor
   - `GET  /api/v1/doctores` — listar doctores
   - `GET  /api/v1/doctores/{id}` — obtener doctor por ID

5.4. Crear `app/presentation/routers/paciente_router.py`:
   - `POST /api/v1/pacientes` — registrar paciente
   - `GET  /api/v1/pacientes` — listar pacientes
   - `GET  /api/v1/pacientes/{id}` — obtener paciente por ID

5.5. Crear `app/presentation/routers/cita_router.py`:
   - `POST   /api/v1/citas` — agendar cita
   - `PATCH  /api/v1/citas/{id}/cancelar` — cancelar cita
   - `PATCH  /api/v1/citas/{id}/reprogramar` — reprogramar cita
   - `GET    /api/v1/doctores/{id}/disponibilidad?fecha=YYYY-MM-DD` — consultar disponibilidad
   - `GET    /api/v1/doctores/{id}/citas?activas=true` — citas por doctor
   - `GET    /api/v1/pacientes/{id}/citas?activas=true` — citas por paciente

5.6. Registrar routers en `app/main.py` con prefijo `/api/v1`.

5.7. Registrar exception handlers globales en `app/main.py`.

### Entregable
- API funcional completa. Se puede probar con Swagger UI en `/docs`.

---

## FASE 6 — Testing

**Objetivo:** Cobertura de tests unitarios e integración para garantizar calidad.

### Pasos

6.1. Crear `tests/conftest.py`:
   - Fixture: base de datos SQLite en memoria
   - Fixture: session de test con rollback automático
   - Fixture: `TestClient` de FastAPI apuntando a la DB de test
   - Fixture: factories para crear doctores/pacientes/citas de prueba

6.2. Crear `tests/unit/test_rules.py`:
   - Test: `validar_fecha_futura` lanza error con fecha pasada
   - Test: `validar_fecha_futura` pasa con fecha futura
   - Test: `validar_no_solapamiento` detecta conflicto correctamente
   - Test: `validar_no_solapamiento` permite citas sin conflicto
   - Test: `validar_transicion_estado` permite PROGRAMADA → CANCELADA
   - Test: `validar_transicion_estado` rechaza CANCELADA → PROGRAMADA
   - Test: `validar_email` rechaza formatos inválidos

6.3. Crear `tests/unit/test_doctor_service.py`:
   - Test: registrar doctor exitosamente
   - Test: registrar doctor con licencia duplicada lanza error

6.4. Crear `tests/unit/test_paciente_service.py`:
   - Test: registrar paciente exitosamente
   - Test: registrar paciente con documento duplicado lanza error
   - Test: registrar paciente con email inválido lanza error

6.5. Crear `tests/unit/test_cita_service.py`:
   - Test: agendar cita exitosamente
   - Test: agendar cita en el pasado lanza error
   - Test: agendar cita con solapamiento lanza error
   - Test: cancelar cita activa exitosamente
   - Test: cancelar cita ya cancelada lanza error
   - Test: reprogramar cita crea nueva cita y marca la original
   - Test: consultar disponibilidad retorna slots correctos

6.6. Crear `tests/integration/test_doctor_api.py`:
   - Test: POST crear doctor → 201
   - Test: POST licencia duplicada → 409
   - Test: GET listar doctores → 200
   - Test: GET doctor inexistente → 404

6.7. Crear `tests/integration/test_paciente_api.py`:
   - Test: POST crear paciente → 201
   - Test: POST documento duplicado → 409
   - Test: GET listar pacientes → 200

6.8. Crear `tests/integration/test_cita_api.py`:
   - Test: POST agendar cita → 201
   - Test: POST cita en pasado → 422
   - Test: POST cita solapada → 409
   - Test: PATCH cancelar → 200
   - Test: PATCH reprogramar → 200/201
   - Test: GET disponibilidad → 200
   - Test: GET citas por doctor → 200

### Entregable
- Suite de tests ejecutable con `pytest -v`.
- Cobertura mínima de las reglas de negocio críticas.

---

## FASE 7 — Documentación y Cierre

**Objetivo:** Proyecto listo para ser clonado, ejecutado y extendido por cualquier desarrollador.

### Pasos

7.1. Crear `README.md` con:
   - Descripción del proyecto
   - Arquitectura (diagrama en texto)
   - Requisitos previos (Python 3.11+)
   - Instrucciones de instalación y ejecución
   - Cómo ejecutar tests
   - Cómo cambiar de SQLite a PostgreSQL (cambiar `DATABASE_URL` + instalar `psycopg2`)
   - Tabla de endpoints disponibles

7.2. Verificar que la documentación de Swagger (`/docs`) se genere correctamente con:
   - Descripciones en cada endpoint
   - Ejemplos en los schemas Pydantic
   - Tags agrupando por recurso (Doctores, Pacientes, Citas)

7.3. Agregar instrucciones de Alembic:
   - Cómo generar nueva migración
   - Cómo aplicar migraciones

7.4. Revisar y limpiar:
   - Eliminar código muerto
   - Verificar que todos los imports sean correctos
   - Verificar que `pyproject.toml` tenga todas las dependencias

---

## Resumen de Fases

| Fase | Nombre                        | Dependencias | Complejidad |
|------|-------------------------------|--------------|-------------|
| 1    | Inicialización y configuración | Ninguna      | Baja        |
| 2    | Capa de Dominio               | Fase 1       | Media       |
| 3    | Capa de Repositorio           | Fases 1, 2   | Media       |
| 4    | Capa de Aplicación (Servicios)| Fases 2, 3   | Alta        |
| 5    | Capa de Presentación (API)    | Fases 3, 4   | Media       |
| 6    | Testing                       | Fases 1-5    | Alta        |
| 7    | Documentación y Cierre        | Fases 1-6    | Baja        |

---

## Notas Importantes

- **Configurabilidad:** La duración de la cita debe leerse de una variable de entorno (`DURACION_CITA_MINUTOS`) con default de 30 minutos, usando `pydantic-settings`.
- **Versionado de API:** Todos los endpoints bajo `/api/v1/` para facilitar evolución futura.
- **Separación estricta:** La capa de dominio no importa nada de SQLAlchemy ni FastAPI. Los servicios no acceden a `session` directamente, solo a repositorios.
- **Errores claros:** Cada excepción de dominio se traduce a un código HTTP específico con un mensaje descriptivo en JSON.
- **Idempotencia:** Cancelar una cita ya cancelada retorna error claro, no falla silenciosamente.
