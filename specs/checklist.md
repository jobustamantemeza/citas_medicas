# Checklist de Progreso — Sistema de Citas Médicas

> Referencia: `specs/plan-desarrollo.md`

---

## FASE 1 — Inicialización del proyecto y configuración

- [x] 1.1 Crear estructura de carpetas y archivos `__init__.py`
- [x] 1.2 Crear `pyproject.toml` con dependencias (fastapi, sqlalchemy, pydantic, alembic, pytest, httpx, uvicorn)
- [x] 1.3 Crear `app/config.py` con `DATABASE_URL` y `DURACION_CITA_MINUTOS`
- [x] 1.4 Crear `app/infrastructure/database.py` (engine, session, Base, create_tables)
- [x] 1.5 Crear `app/main.py` con FastAPI, lifespan y endpoint `/health`
- [x] 1.6 Verificar que el servidor levanta sin errores

---

## FASE 2 — Capa de Dominio

- [x] 2.1 Crear `app/domain/enums.py` con `EstadoCita`
- [x] 2.2 Crear `app/domain/entities.py` (Doctor, Paciente, Cita como dataclasses)
- [x] 2.3 Crear `app/domain/exceptions.py` (CitaSolapadaError, CitaEnPasadoError, etc.)
- [x] 2.4 Crear `app/domain/rules.py` (validar_no_solapamiento, validar_fecha_futura, validar_transicion_estado, validar_email, calcular_fin_cita)

---

## FASE 3 — Capa de Repositorio

- [x] 3.1 Crear `app/infrastructure/models.py` (DoctorModel, PacienteModel, CitaModel)
- [x] 3.2 Crear `app/infrastructure/repositories/base.py` (repositorio abstracto)
- [x] 3.3 Crear `app/infrastructure/repositories/doctor_repo.py`
- [x] 3.4 Crear `app/infrastructure/repositories/paciente_repo.py`
- [x] 3.5 Crear `app/infrastructure/repositories/cita_repo.py`
- [x] 3.6 Configurar Alembic y generar migración inicial

---

## FASE 4 — Capa de Aplicación (Servicios)

- [x] 4.1 Crear `app/application/schemas.py` (DTOs Pydantic para request/response)
- [x] 4.2 Crear `app/application/doctor_service.py` (registrar, obtener, listar)
- [x] 4.3 Crear `app/application/paciente_service.py` (registrar, obtener, listar)
- [x] 4.4 Crear `app/application/cita_service.py` (agendar, cancelar, reprogramar, disponibilidad, listar)

---

## FASE 5 — Capa de Presentación (API REST)

- [x] 5.1 Crear `app/presentation/dependencies.py` (get_db, get_services)
- [x] 5.2 Crear `app/presentation/error_handlers.py` (excepciones dominio → HTTP)
- [x] 5.3 Crear `app/presentation/routers/doctor_router.py` (POST, GET, GET/:id)
- [x] 5.4 Crear `app/presentation/routers/paciente_router.py` (POST, GET, GET/:id)
- [x] 5.5 Crear `app/presentation/routers/cita_router.py` (POST, PATCH cancelar, PATCH reprogramar, GET disponibilidad, GET por doctor/paciente)
- [x] 5.6 Registrar routers y error handlers en `app/main.py`

---

## FASE 6 — Testing

- [x] 6.1 Crear `tests/conftest.py` (fixtures: DB en memoria, TestClient, factories)
- [x] 6.2 Tests unitarios: reglas de negocio (`test_rules.py`)
- [x] 6.3 Tests unitarios: servicio de doctores (`test_doctor_service.py`)
- [x] 6.4 Tests unitarios: servicio de pacientes (`test_paciente_service.py`)
- [x] 6.5 Tests unitarios: servicio de citas (`test_cita_service.py`)
- [x] 6.6 Tests integración: API de doctores (`test_doctor_api.py`)
- [x] 6.7 Tests integración: API de pacientes (`test_paciente_api.py`)
- [x] 6.8 Tests integración: API de citas (`test_cita_api.py`)

---

## FASE 7 — Documentación y Cierre

- [x] 7.1 Crear `README.md` (descripción, arquitectura, instalación, ejecución, tests, PostgreSQL)
- [x] 7.2 Verificar Swagger `/docs` (descripciones, ejemplos, tags)
- [x] 7.3 Agregar instrucciones de Alembic en README
- [x] 7.4 Revisión final: imports, código muerto, dependencias completas

---

## Resumen de Estado

| Fase | Estado | Progreso |
|------|--------|----------|
| 1 — Inicialización       | ✅ Completada | 6/6 |
| 2 — Dominio              | ✅ Completada | 4/4 |
| 3 — Repositorio          | ✅ Completada | 6/6 |
| 4 — Aplicación           | ✅ Completada | 4/4 |
| 5 — Presentación         | ✅ Completada | 6/6 |
| 6 — Testing              | ✅ Completada | 8/8 |
| 7 — Documentación        | ✅ Completada | 4/4 |
| **Total**                 | **✅ Completado** | **38/38** |
