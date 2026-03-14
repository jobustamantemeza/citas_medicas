# Prompt para generar un sistema de gestión de citas médicas en Python

## Contexto
Estás desarrollando un **sistema backend para la gestión de citas médicas**.  
El sistema debe permitir registrar médicos y pacientes, agendar citas, consultar disponibilidad y gestionar cambios de estado de las citas.

El proyecto debe implementarse en **Python** siguiendo buenas prácticas de ingeniería de software, usando **Arquitectura en Capas (Layered Architecture)** para separar responsabilidades:

**Presentación → Aplicación → Dominio/Negocio → Repositorio (Data Layer)**

La API debe construirse preferiblemente con **FastAPI**, usando **SQLAlchemy** para persistencia y **SQLite por defecto** (con instrucciones para cambiar a PostgreSQL).

El código debe ser **ejecutable, testeable y organizado como un proyecto real de producción**.

---

# Rol
Actúa como un **Arquitecto de Software y Desarrollador Senior en Python especializado en backend y diseño limpio (Clean Architecture / Layered Architecture)**.

Debes:

- Diseñar la arquitectura del proyecto
- Definir entidades de dominio
- Implementar la API REST
- Implementar capa de aplicación y repositorios
- Implementar reglas de negocio
- Crear pruebas automatizadas
- Documentar el proyecto

Prioriza:

- claridad arquitectónica
- separación de responsabilidades
- código mantenible
- validaciones correctas
- ejemplos ejecutables

---

# Tarea
Diseña e implementa un **proyecto completo en Python** que cumpla los siguientes requisitos.

---

# 1. Funcionalidades requeridas

Implementar:

### Registrar médicos
Campos:

- nombre
- especialidad
- número de licencia (**único**)

### Registrar pacientes

Campos:

- nombre
- documento (**único**)
- correo electrónico

### Gestión de citas

El sistema debe permitir:

- Agendar cita (paciente, médico, fecha y hora)
- Cancelar cita
- Reprogramar cita
- Consultar disponibilidad de un médico
- Listar citas:
  - por médico
  - por paciente
  - citas activas

La **duración estándar de las citas debe ser configurable** (por ejemplo 30 minutos).

---

# 2. Reglas de negocio obligatorias

Implementar validaciones en la capa de dominio o aplicación.

Reglas:

- Un médico **no puede tener citas superpuestas**
- No se pueden agendar **citas en el pasado**
- Sólo se puede **cancelar una cita activa**
- Validar duración estándar de cita
- Validar **formato de email**
- Validar que la especialidad del médico sea adecuada (si se solicita)

Estados mínimos de cita:
