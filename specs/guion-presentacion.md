# Guion de Presentación — Arquitectura en Capas: Registrar Cita Médica

---

## Introducción (2 min)

Vamos a presentar cómo se diseñó un sistema de gestión de citas médicas usando **Arquitectura en Capas (Layered Architecture)**.

El objetivo es mostrar:
- Cómo se divide la responsabilidad entre capas
- Cómo fluye una operación concreta (`Registrar Cita Médica`) a través de cada capa
- Cómo se garantiza el desacoplamiento entre ellas

**Stack:** Python, FastAPI, SQLAlchemy, SQLite

---

## 1. Diagrama de Capas (5 min)

### Diagrama general

```
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                        │
│                   (app/presentation/)                           │
│                                                                 │
│  Routers FastAPI — recibe HTTP, valida entrada, delega al      │
│  servicio y devuelve respuesta HTTP.                           │
│                                                                 │
│  Conoce: FastAPI, Pydantic schemas, Services                   │
│  NO conoce: SQLAlchemy, Base de datos, Reglas de negocio       │
└────────────────────────────┬────────────────────────────────────┘
                             │ llama a
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA DE APLICACIÓN                           │
│                   (app/application/)                            │
│                                                                 │
│  Services — orquesta el flujo: consulta repos, aplica reglas   │
│  de dominio y persiste el resultado.                           │
│                                                                 │
│  Conoce: Repositories, Domain Rules, Schemas                   │
│  NO conoce: FastAPI, HTTP, Request/Response                    │
└────────────┬──────────────────────────────────┬────────────────┘
             │ aplica reglas de                  │ consulta/persiste
             ▼                                   ▼
┌─────────────────────────────┐  ┌───────────────────────────────┐
│     CAPA DE DOMINIO         │  │   CAPA DE INFRAESTRUCTURA     │
│    (app/domain/)            │  │   (app/infrastructure/)       │
│                             │  │                               │
│  Entidades, Enums,          │  │  Modelos SQLAlchemy,          │
│  Excepciones, Reglas        │  │  Repositories, DB config      │
│  de negocio puras.          │  │                               │
│                             │  │  Conoce: SQLAlchemy, DB       │
│  NO conoce: nada externo.   │  │  NO conoce: FastAPI, HTTP     │
│  Sin imports de frameworks. │  │                               │
└─────────────────────────────┘  └───────────────────────────────┘
```

### Regla clave

> Cada capa solo depende de la capa inmediatamente inferior. Nunca al revés.

---

## 2. Responsabilidades por Capa (5 min)

### Capa de Presentación (`app/presentation/`)

| # | Responsabilidad | Ejemplo concreto |
|---|---|---|
| 1 | **Recibir y enrutar peticiones HTTP** | `POST /api/v1/citas` llega al router y se mapea a la función `agendar_cita()` |
| 2 | **Validar formato de entrada** | Pydantic valida que `fecha_hora` sea un datetime válido y que `doctor_id` sea un entero |
| 3 | **Traducir excepciones de dominio a respuestas HTTP** | `CitaSolapadaError` se convierte en HTTP 409 con mensaje JSON descriptivo |

Lo que **NO hace**: no valida reglas de negocio, no accede a la base de datos, no sabe qué es SQLAlchemy.

### Capa de Aplicación (`app/application/`)

| # | Responsabilidad | Ejemplo concreto |
|---|---|---|
| 1 | **Orquestar el caso de uso completo** | `CitaService.agendar()` coordina la verificación del doctor, la validación de fecha y la persistencia |
| 2 | **Invocar reglas de dominio** | Llama a `validar_fecha_futura()` y `validar_no_solapamiento()` del módulo de dominio |
| 3 | **Coordinar múltiples repositorios** | Consulta `DoctorRepository`, `PacienteRepository` y `CitaRepository` en un solo flujo |

Lo que **NO hace**: no define reglas de negocio (las consume), no sabe de HTTP ni de códigos de estado.

### Capa de Dominio (`app/domain/`)

| # | Responsabilidad | Ejemplo concreto |
|---|---|---|
| 1 | **Definir las reglas de negocio** | `validar_no_solapamiento()` — un médico no puede tener dos citas al mismo tiempo |
| 2 | **Modelar las entidades del negocio** | `Cita` tiene `paciente_id`, `doctor_id`, `fecha_hora`, `estado` con sus invariantes |
| 3 | **Definir excepciones específicas del dominio** | `CitaSolapadaError`, `CitaEnPasadoError`, `EstadoCitaInvalidoError` con mensajes claros |

Lo que **NO hace**: no importa SQLAlchemy, FastAPI ni ningún framework. Es **Python puro**.

### Capa de Infraestructura (`app/infrastructure/`)

| # | Responsabilidad | Ejemplo concreto |
|---|---|---|
| 1 | **Persistir y recuperar datos** | `CitaRepository.create()` guarda la cita en la base de datos |
| 2 | **Definir el esquema de la base de datos** | `CitaModel` mapea la tabla `citas` con columnas, FKs e índices |
| 3 | **Consultar datos con filtros específicos** | `get_citas_doctor_en_rango()` busca citas activas que se solapan con un horario dado |

Lo que **NO hace**: no valida reglas de negocio, no sabe de HTTP.

---

## 3. Caso de uso: Registrar Cita Médica — paso a paso (10 min)

### Flujo completo

```
Cliente (Postman/Frontend)
    │
    │  POST /api/v1/citas
    │  { "paciente_id": 1, "doctor_id": 1, "fecha_hora": "2026-03-20T10:00:00" }
    │
    ▼
┌─ PRESENTACIÓN ──────────────────────────────────────────────────┐
│                                                                  │
│  1. FastAPI recibe el request                                    │
│  2. Pydantic valida el JSON → CitaCreate(paciente_id, doctor_id, │
│     fecha_hora)                                                  │
│  3. Inyecta CitaService via Depends()                            │
│  4. Llama a service.agendar(data)                                │
│                                                                  │
└──────────────────────────┬───────────────────────────────────────┘
                           ▼
┌─ APLICACIÓN ────────────────────────────────────────────────────┐
│                                                                  │
│  CitaService.agendar(data):                                      │
│                                                                  │
│  5. doctor_repo.get_by_id(1) → ¿existe el doctor? ✓             │
│  6. paciente_repo.get_by_id(1) → ¿existe el paciente? ✓         │
│  7. DOMINIO: validar_fecha_futura(fecha_hora) ✓                  │
│  8. cita_repo.get_citas_doctor_en_rango(1, 10:00, 10:30)        │
│  9. DOMINIO: validar_no_solapamiento(citas, fecha, 30min) ✓     │
│  10. cita_repo.create(nueva_cita)                                │
│                                                                  │
└──────────┬────────────────────────────────┬──────────────────────┘
           ▼                                ▼
┌─ DOMINIO ──────────────────┐  ┌─ INFRAESTRUCTURA ──────────────┐
│                             │  │                                │
│  validar_fecha_futura():    │  │  get_citas_doctor_en_rango():  │
│  → fecha > ahora? ✓        │  │  → SELECT * FROM citas         │
│                             │  │    WHERE doctor_id = 1         │
│  validar_no_solapamiento(): │  │    AND estado = 'PROGRAMADA'   │
│  → ¿nuevo rango se solapa   │  │    AND fecha_hora < 10:30      │
│    con alguna cita activa?  │  │                                │
│  → No hay conflicto ✓       │  │  create():                     │
│                             │  │  → INSERT INTO citas (...)     │
└─────────────────────────────┘  └────────────────────────────────┘
                           │
                           ▼
┌─ PRESENTACIÓN (respuesta) ──────────────────────────────────────┐
│                                                                  │
│  11. Serializa con CitaResponse (Pydantic)                       │
│  12. Retorna HTTP 201 Created:                                   │
│      {                                                           │
│        "id": 1,                                                  │
│        "paciente_id": 1,                                         │
│        "doctor_id": 1,                                           │
│        "fecha_hora": "2026-03-20T10:00:00",                      │
│        "duracion_minutos": 30,                                   │
│        "estado": "PROGRAMADA"                                    │
│      }                                                           │
└──────────────────────────────────────────────────────────────────┘
```

### ¿Qué pasa si hay un error?

```
Caso: el médico ya tiene cita a las 10:00

INFRAESTRUCTURA  →  devuelve la cita existente a las 10:00
DOMINIO          →  validar_no_solapamiento() lanza CitaSolapadaError
APLICACIÓN       →  no atrapa la excepción, la deja subir
PRESENTACIÓN     →  error_handler captura CitaSolapadaError → HTTP 409
                     { "detail": "El médico ya tiene una cita entre 10:00 y 10:30." }
```

---

## 4. Desacoplamiento — ¿Cómo se asegura? (5 min)

### Estrategia 1: La capa de dominio no importa ningún framework

```python
# app/domain/rules.py
# Solo usa: datetime, re (librería estándar de Python)
# NO importa: SQLAlchemy, FastAPI, Pydantic

def validar_no_solapamiento(citas_existentes, nueva_fecha, duracion):
    # lógica pura con tipos nativos de Python
```

**Beneficio:** Las reglas de negocio se pueden testear sin base de datos ni servidor HTTP. Se ejecutan en milisegundos.

### Estrategia 2: Inyección de dependencias

```python
# El servicio recibe sus repositorios por constructor
class CitaService:
    def __init__(self, cita_repo, doctor_repo, paciente_repo):
        self.cita_repo = cita_repo  # se inyecta, no se crea internamente

# FastAPI inyecta todo vía Depends()
def get_cita_service(db: Session):
    return CitaService(
        cita_repo=CitaRepository(db),
        doctor_repo=DoctorRepository(db),
        paciente_repo=PacienteRepository(db),
    )
```

**Beneficio:** En tests podemos inyectar una DB en memoria. En producción, PostgreSQL. El servicio no cambia.

### Estrategia 3: Los errores fluyen como excepciones de dominio

```
Dominio define:     CitaSolapadaError (no sabe de HTTP)
Presentación mapea: CitaSolapadaError → HTTP 409

# error_handlers.py
EXCEPTION_STATUS_MAP = {
    EntidadNoEncontradaError: 404,
    CitaSolapadaError: 409,
    CitaEnPasadoError: 422,
}
```

**Beneficio:** El dominio no sabe qué es un código HTTP. Si mañana cambiamos de REST a GraphQL, las reglas siguen igual.

### Estrategia 4: Los DTOs viven en la capa de aplicación, separados de los modelos de DB

```
PacienteCreate (Pydantic) ≠ PacienteModel (SQLAlchemy)
CitaResponse (Pydantic)   ≠ CitaModel (SQLAlchemy)
```

**Beneficio:** Podemos cambiar la estructura de la tabla sin afectar la API pública, y viceversa.

---

## 5. Prueba de desacoplamiento: los tests lo demuestran (3 min)

```
58 tests — 100% pasando

Tests unitarios (sin base de datos, sin HTTP):
  ✓ test_fecha_pasada_lanza_error
  ✓ test_detecta_conflicto_solapamiento
  ✓ test_cancelada_a_programada_falla
  ✓ test_email_invalido_rechazado

Tests de integración (con DB en memoria + TestClient):
  ✓ POST crear doctor → 201
  ✓ POST cita solapada → 409
  ✓ PATCH cancelar → 200
  ✓ GET disponibilidad → slots correctos
```

Los tests unitarios prueban el dominio **aislado**. Los tests de integración prueban el flujo completo. Eso es posible **porque las capas están desacopladas**.

---

## 6. Resumen y cierre (2 min)

| Pregunta | Respuesta |
|---|---|
| ¿Dónde viven las reglas de negocio? | En `app/domain/rules.py` — Python puro, sin frameworks |
| ¿Dónde se accede a la base de datos? | Solo en `app/infrastructure/repositories/` |
| ¿Dónde se manejan los endpoints HTTP? | Solo en `app/presentation/routers/` |
| ¿Quién orquesta todo? | `app/application/services/` — conecta dominio con repos |
| ¿Cómo se asegura el desacoplamiento? | Inyección de dependencias, excepciones de dominio, DTOs separados de modelos |
| ¿Si cambio de SQLite a PostgreSQL? | Solo cambio una variable de entorno. Ningún servicio ni regla cambia |
| ¿Si cambio de REST a GraphQL? | Solo reescribo la capa de presentación. Dominio y repos quedan igual |

> **Conclusión:** La arquitectura en capas nos permite que cada parte del sistema cambie de forma independiente, se teste aisladamente y se entienda por separado.
