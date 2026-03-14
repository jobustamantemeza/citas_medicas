# Arquitectura en Capas aplicada a un Sistema de Gestión de Citas Médicas

**Materia:** Ingeniería de Software
**Tema:** Arquitectura en Capas (Layered Architecture)
**Caso de estudio:** Registro de cita médica

---

## 1. Introducción

El presente documento describe el diseño e implementación de un sistema backend para la gestión de citas médicas, desarrollado en Python utilizando el framework FastAPI, el ORM SQLAlchemy y SQLite como motor de base de datos.

El propósito del trabajo es demostrar cómo la Arquitectura en Capas permite organizar un sistema de software separando claramente las responsabilidades de cada componente, de manera que el código resultante sea mantenible, testeable y extensible.

El sistema permite registrar médicos y pacientes, agendar citas, cancelarlas, reprogramarlas y consultar la disponibilidad de un médico en un día determinado. A lo largo del documento se utilizará el caso de uso "Registrar Cita Médica" como hilo conductor para explicar el rol de cada capa y la interacción entre ellas.

---

## 2. Arquitectura general del sistema

La arquitectura del sistema sigue el patrón de Arquitectura en Capas (Layered Architecture), dividiendo el código en cuatro niveles con responsabilidades bien definidas:

```
┌─────────────────────────────────────────────────────────┐
│                 CAPA DE PRESENTACIÓN                    │
│              (app/presentation/)                        │
│                                                         │
│  Recibe peticiones HTTP, valida la estructura de los    │
│  datos de entrada y delega el procesamiento a la capa   │
│  de aplicación. Traduce las excepciones del dominio     │
│  a respuestas HTTP con códigos de estado apropiados.    │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 CAPA DE APLICACIÓN                      │
│              (app/application/)                         │
│                                                         │
│  Contiene los servicios que orquestan cada caso de uso.  │
│  Consulta repositorios, invoca reglas del dominio y     │
│  coordina la persistencia de los resultados.            │
└──────────┬──────────────────────────────┬───────────────┘
           │                              │
           ▼                              ▼
┌──────────────────────────┐  ┌───────────────────────────┐
│    CAPA DE DOMINIO       │  │ CAPA DE INFRAESTRUCTURA   │
│   (app/domain/)          │  │ (app/infrastructure/)     │
│                          │  │                           │
│  Entidades, reglas de    │  │  Modelos de base de datos,│
│  negocio y excepciones   │  │  repositorios y           │
│  propias del problema.   │  │  configuración de acceso  │
│  No depende de ningún    │  │  a datos.                 │
│  framework externo.      │  │                           │
└──────────────────────────┘  └───────────────────────────┘
```

El principio fundamental que rige esta organización es que **cada capa solo conoce y depende de la capa inmediatamente inferior, nunca al revés**. Esto garantiza que los cambios en una capa no propaguen efectos no deseados a las demás.

---

## 3. Descripción de cada capa y sus responsabilidades

### 3.1. Capa de Presentación

La capa de presentación es el punto de entrada al sistema. Es la única capa que tiene conocimiento del protocolo HTTP y del framework web utilizado (FastAPI). Su función es actuar como intermediaria entre el mundo exterior (clientes, navegadores, aplicaciones móviles) y la lógica interna del sistema.

**Responsabilidades principales:**

1. **Recibir y enrutar las peticiones HTTP.** Cada endpoint está asociado a una URL y un método HTTP específico. Por ejemplo, una petición `POST /api/v1/citas` es recibida por el router de citas y dirigida a la función correspondiente.

2. **Validar la estructura de los datos de entrada.** Antes de que los datos lleguen a la lógica de negocio, se valida que tengan el formato correcto. Esto se logra mediante esquemas Pydantic que verifican automáticamente que los campos obligatorios estén presentes y que sus tipos sean los esperados. Por ejemplo, que `fecha_hora` sea una fecha válida y que `doctor_id` sea un número entero.

3. **Traducir las excepciones del dominio a respuestas HTTP.** Cuando la lógica de negocio detecta un error (por ejemplo, que un médico ya tiene una cita en ese horario), lanza una excepción propia del dominio. La capa de presentación captura esa excepción y la convierte en una respuesta HTTP con el código de estado apropiado y un mensaje descriptivo en formato JSON.

   El mapeo de excepciones a códigos HTTP es el siguiente:

   | Excepción de dominio | Código HTTP | Significado |
   |---|---|---|
   | EntidadNoEncontradaError | 404 Not Found | El médico, paciente o cita no existe |
   | DuplicadoError | 409 Conflict | Ya existe un registro con ese valor único |
   | CitaSolapadaError | 409 Conflict | El médico ya tiene una cita en ese horario |
   | CitaEnPasadoError | 422 Unprocessable Entity | La fecha solicitada ya pasó |
   | EstadoCitaInvalidoError | 422 Unprocessable Entity | La transición de estado no es válida |

**Lo que esta capa no hace:** no contiene reglas de negocio, no accede directamente a la base de datos y no tiene conocimiento de cómo se almacenan los datos.

### 3.2. Capa de Aplicación

La capa de aplicación contiene los servicios que representan los casos de uso del sistema. Su función es orquestar el flujo de una operación completa: verificar precondiciones consultando los repositorios, invocar las reglas de negocio del dominio y coordinar la persistencia del resultado.

**Responsabilidades principales:**

1. **Orquestar el flujo completo de cada caso de uso.** Para el caso de registrar una cita, el servicio `CitaService` coordina la verificación de que el médico y el paciente existan, la validación de la fecha, la verificación de que no haya solapamiento de horarios y finalmente la creación de la cita en la base de datos.

2. **Invocar las reglas de negocio definidas en la capa de dominio.** El servicio no implementa las reglas por sí mismo, sino que las delega a funciones puras del módulo de dominio. Por ejemplo, llama a `validar_fecha_futura()` para asegurar que la cita no sea en el pasado y a `validar_no_solapamiento()` para verificar que el médico no tenga conflictos de horario.

3. **Coordinar la interacción entre múltiples repositorios.** Un solo caso de uso puede requerir consultar datos de diferentes fuentes. Para agendar una cita, el servicio necesita acceder al repositorio de doctores, al de pacientes y al de citas, manteniendo la coherencia del flujo.

**Lo que esta capa no hace:** no define las reglas de negocio (las consume desde el dominio), no tiene conocimiento de HTTP ni de códigos de estado, y no accede a la base de datos directamente (lo hace a través de los repositorios).

### 3.3. Capa de Dominio

La capa de dominio es el corazón del sistema. Contiene la representación del problema de negocio en forma de entidades, reglas y excepciones. Su característica más importante es que **no depende de ningún framework ni tecnología externa**: está escrita en Python puro, utilizando únicamente la librería estándar del lenguaje.

**Responsabilidades principales:**

1. **Definir las reglas de negocio.** Estas reglas son funciones puras que reciben datos y validan condiciones del negocio. La función `validar_no_solapamiento()` recibe la lista de citas existentes de un médico y la fecha propuesta, y determina si hay un conflicto de horario. La función `validar_fecha_futura()` verifica que no se intente agendar una cita en el pasado. La función `validar_transicion_estado()` asegura que solo se permitan cambios de estado válidos (por ejemplo, una cita cancelada no puede volver a programarse).

2. **Modelar las entidades del negocio.** Las entidades `Doctor`, `Paciente` y `Cita` están definidas como dataclasses de Python con los atributos que representan el concepto de negocio. La entidad `Cita` tiene un estado que solo puede tomar los valores `PROGRAMADA`, `COMPLETADA`, `CANCELADA` o `REPROGRAMADA`, y las transiciones entre estos estados están explícitamente definidas.

3. **Definir excepciones específicas del dominio.** Cada error de negocio tiene su propia excepción con un nombre descriptivo: `CitaSolapadaError`, `CitaEnPasadoError`, `EstadoCitaInvalidoError`, `DuplicadoError`, `EntidadNoEncontradaError`. Estas excepciones no contienen información sobre HTTP ni sobre la infraestructura; simplemente describen qué regla de negocio se violó.

**Lo que esta capa no hace:** no importa SQLAlchemy, FastAPI ni ningún otro framework. No sabe cómo se almacenan los datos ni cómo se comunican con el exterior.

### 3.4. Capa de Infraestructura

La capa de infraestructura se encarga de todo lo relacionado con la persistencia de datos. Es la única capa que tiene conocimiento de SQLAlchemy, de la estructura de las tablas y de cómo se ejecutan las consultas a la base de datos.

**Responsabilidades principales:**

1. **Persistir y recuperar datos.** Los repositorios ofrecen métodos para crear, leer, actualizar y eliminar registros. El método `create()` del repositorio de citas inserta una nueva fila en la tabla `citas` y retorna el objeto creado con su identificador asignado.

2. **Definir el esquema de la base de datos.** Los modelos SQLAlchemy (`DoctorModel`, `PacienteModel`, `CitaModel`) definen la estructura de las tablas, incluyendo columnas, tipos de datos, claves primarias, claves foráneas y restricciones de unicidad. La tabla `citas` tiene relaciones de clave foránea con las tablas `doctores` y `pacientes`.

3. **Ejecutar consultas especializadas.** Además de las operaciones CRUD básicas, los repositorios implementan consultas específicas del negocio. Por ejemplo, `get_citas_doctor_en_rango()` busca todas las citas activas de un médico en un rango de fechas determinado, lo cual es necesario para validar si hay solapamiento antes de agendar una nueva cita.

**Lo que esta capa no hace:** no valida reglas de negocio y no tiene conocimiento del protocolo HTTP.

---

## 4. Caso de uso: Registrar Cita Médica

Para ilustrar la interacción entre capas, se describe a continuación el flujo completo que ocurre cuando un cliente envía una petición para agendar una cita médica.

### 4.1. Petición del cliente

El cliente envía la siguiente petición HTTP:

```
POST /api/v1/citas
Content-Type: application/json

{
    "paciente_id": 1,
    "doctor_id": 1,
    "fecha_hora": "2026-03-20T10:00:00"
}
```

### 4.2. Procesamiento en la Capa de Presentación

El router de citas recibe la petición y realiza las siguientes acciones:

- FastAPI identifica que la URL y el método corresponden al endpoint de agendar cita.
- Pydantic deserializa el cuerpo JSON y lo valida contra el esquema `CitaCreate`, verificando que los campos requeridos estén presentes y tengan los tipos correctos.
- El mecanismo de inyección de dependencias de FastAPI proporciona una instancia de `CitaService` ya configurada con los repositorios necesarios.
- Se invoca el método `service.agendar(data)`, delegando toda la lógica al servicio de la capa de aplicación.

### 4.3. Procesamiento en la Capa de Aplicación

El método `CitaService.agendar()` ejecuta el siguiente flujo de orquestación:

1. Consulta el repositorio de doctores para verificar que el médico con id 1 existe. Si no existe, lanza `EntidadNoEncontradaError`.
2. Consulta el repositorio de pacientes para verificar que el paciente con id 1 existe. Si no existe, lanza `EntidadNoEncontradaError`.
3. Invoca la regla de dominio `validar_fecha_futura()` para asegurar que la fecha solicitada no haya pasado ya.
4. Consulta el repositorio de citas para obtener las citas activas del médico en el rango horario de la nueva cita (10:00 a 10:30, considerando la duración estándar de 30 minutos).
5. Invoca la regla de dominio `validar_no_solapamiento()` con las citas existentes y la nueva fecha propuesta.
6. Si todas las validaciones pasan, crea el objeto de cita con estado `PROGRAMADA` y lo persiste a través del repositorio.

### 4.4. Procesamiento en la Capa de Dominio

Las reglas de negocio se ejecutan como funciones puras:

- `validar_fecha_futura()` compara la fecha recibida con la fecha y hora actuales. Si la fecha es anterior al momento presente, lanza `CitaEnPasadoError`.
- `validar_no_solapamiento()` recibe la lista de citas existentes del médico (como tuplas de fecha de inicio y duración) y calcula si el rango de la nueva cita se superpone con alguna existente. Si detecta conflicto, lanza `CitaSolapadaError`.

### 4.5. Procesamiento en la Capa de Infraestructura

Los repositorios ejecutan las operaciones de base de datos:

- `get_by_id()` ejecuta una consulta SQL para buscar al médico y al paciente por su clave primaria.
- `get_citas_doctor_en_rango()` ejecuta una consulta filtrada que busca citas del médico con estado `PROGRAMADA` cuya fecha sea anterior al fin del rango propuesto.
- `create()` inserta una nueva fila en la tabla `citas` con los datos proporcionados.

### 4.6. Respuesta al cliente

Si todo el proceso es exitoso, la capa de presentación serializa el resultado usando el esquema `CitaResponse` y retorna una respuesta HTTP con código 201 (Created):

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

### 4.7. Flujo alternativo: error por solapamiento

Si el médico ya tiene una cita a las 10:00, el flujo cambia de la siguiente manera:

1. La capa de infraestructura retorna la cita existente a las 10:00.
2. La capa de dominio, al ejecutar `validar_no_solapamiento()`, detecta el conflicto y lanza `CitaSolapadaError`.
3. La capa de aplicación no captura la excepción y la deja propagarse.
4. La capa de presentación captura la excepción a través del handler de errores registrado, la mapea al código HTTP 409 y retorna la respuesta:

```json
{
    "detail": "El médico ya tiene una cita entre 10:00 y 10:30."
}
```

Este flujo demuestra que cada capa cumple su rol sin invadir las responsabilidades de las demás: la infraestructura solo recupera datos, el dominio solo valida reglas, la aplicación solo coordina y la presentación solo traduce a HTTP.

---

## 5. Código del caso de uso RegistrarCitaMedica dividido por capas

A continuación se presenta el código real del caso de uso "Registrar Cita Médica", separado por cada capa del sistema, mostrando cómo cada una cumple exclusivamente con su responsabilidad.

### 5.1. Capa de Presentación — Recibir la petición y delegar

El router define el endpoint HTTP y delega inmediatamente al servicio de la capa de aplicación. No contiene lógica de negocio.

```python
# app/presentation/routers/cita_router.py

@router.post(
    "/citas",
    response_model=CitaResponse,
    status_code=status.HTTP_201_CREATED,
)
def agendar_cita(data: CitaCreate, service: CitaServiceDep):
    return service.agendar(data)
```

El esquema `CitaCreate` valida automáticamente la estructura de entrada:

```python
# app/application/schemas.py

class CitaCreate(BaseModel):
    paciente_id: int
    doctor_id: int
    fecha_hora: datetime
```

Si el JSON no tiene los campos requeridos o los tipos no coinciden, Pydantic rechaza la petición antes de que llegue al servicio.

### 5.2. Capa de Aplicación — Orquestar el flujo completo

El servicio coordina las verificaciones, invoca las reglas de dominio y persiste el resultado. Es el director de orquesta del caso de uso.

```python
# app/application/cita_service.py

class CitaService:
    def __init__(self, cita_repo, doctor_repo, paciente_repo):
        self.cita_repo = cita_repo
        self.doctor_repo = doctor_repo
        self.paciente_repo = paciente_repo
        self.duracion = settings.DURACION_CITA_MINUTOS  # 30 min por defecto

    def agendar(self, data: CitaCreate) -> CitaModel:
        # 1. Verificar que el doctor existe
        doctor = self.doctor_repo.get_by_id(data.doctor_id)
        if not doctor:
            raise EntidadNoEncontradaError(
                f"No se encontró el médico con id {data.doctor_id}."
            )

        # 2. Verificar que el paciente existe
        paciente = self.paciente_repo.get_by_id(data.paciente_id)
        if not paciente:
            raise EntidadNoEncontradaError(
                f"No se encontró el paciente con id {data.paciente_id}."
            )

        # 3. Regla de dominio: la fecha debe ser futura
        validar_fecha_futura(data.fecha_hora)

        # 4. Consultar citas existentes del doctor en ese rango
        fin_nueva = calcular_fin_cita(data.fecha_hora, self.duracion)
        citas_existentes = self.cita_repo.get_citas_doctor_en_rango(
            data.doctor_id, data.fecha_hora, fin_nueva
        )

        # 5. Regla de dominio: no debe haber solapamiento
        citas_para_validar = [
            (c.fecha_hora, c.duracion_minutos) for c in citas_existentes
        ]
        validar_no_solapamiento(citas_para_validar, data.fecha_hora, self.duracion)

        # 6. Persistir la nueva cita
        cita = CitaModel(
            paciente_id=data.paciente_id,
            doctor_id=data.doctor_id,
            fecha_hora=data.fecha_hora,
            duracion_minutos=self.duracion,
            estado=EstadoCita.PROGRAMADA,
        )
        return self.cita_repo.create(cita)
```

Nótese que el servicio no sabe cómo se valida el solapamiento (eso es responsabilidad del dominio) ni cómo se ejecuta la consulta SQL (eso es responsabilidad del repositorio). Solo coordina el flujo.

### 5.3. Capa de Dominio — Validar las reglas de negocio

Las funciones del dominio son puras: reciben datos, validan condiciones y lanzan excepciones si se violan. No acceden a bases de datos ni conocen frameworks.

```python
# app/domain/rules.py

def validar_fecha_futura(fecha: datetime) -> None:
    if fecha <= datetime.now():
        raise CitaEnPasadoError("No se pueden agendar citas en el pasado.")


def validar_no_solapamiento(
    citas_existentes: list[tuple[datetime, int]],
    nueva_fecha: datetime,
    duracion: int,
) -> None:
    nuevo_inicio = nueva_fecha
    nuevo_fin = calcular_fin_cita(nueva_fecha, duracion)

    for inicio_existente, dur_existente in citas_existentes:
        fin_existente = calcular_fin_cita(inicio_existente, dur_existente)
        if nuevo_inicio < fin_existente and nuevo_fin > inicio_existente:
            raise CitaSolapadaError(
                f"El médico ya tiene una cita entre "
                f"{inicio_existente.strftime('%H:%M')} y "
                f"{fin_existente.strftime('%H:%M')}."
            )


def calcular_fin_cita(inicio: datetime, duracion_minutos: int) -> datetime:
    return inicio + timedelta(minutes=duracion_minutos)
```

Estas funciones solo importan `datetime` y `timedelta` de la librería estándar de Python. No tienen dependencia de SQLAlchemy, FastAPI ni ninguna otra librería externa.

### 5.4. Capa de Infraestructura — Persistir y consultar datos

El repositorio encapsula el acceso a la base de datos. Es el único lugar donde se escribe SQL (a través de SQLAlchemy).

```python
# app/infrastructure/repositories/cita_repo.py

class CitaRepository(BaseRepository[CitaModel]):
    def __init__(self, session: Session):
        super().__init__(session, CitaModel)

    def get_citas_doctor_en_rango(
        self, doctor_id: int, inicio: datetime, fin: datetime
    ) -> list[CitaModel]:
        return list(
            self.session.query(CitaModel)
            .filter(
                CitaModel.doctor_id == doctor_id,
                CitaModel.estado == EstadoCita.PROGRAMADA,
                CitaModel.fecha_hora < fin,
            )
            .all()
        )
```

```python
# app/infrastructure/repositories/base.py (método heredado)

class BaseRepository:
    def create(self, entity: ModelType) -> ModelType:
        self.session.add(entity)
        self.session.flush()
        self.session.refresh(entity)
        return entity
```

El repositorio no valida si la fecha es futura ni si hay solapamiento; eso no es su responsabilidad. Solo ejecuta las operaciones de lectura y escritura que le solicita la capa de aplicación.

### 5.5. Capa de Presentación — Traducir errores a HTTP

Si alguna regla de dominio falla durante el flujo, la excepción se propaga hasta la capa de presentación, donde un handler centralizado la traduce a una respuesta HTTP:

```python
# app/presentation/error_handlers.py

EXCEPTION_STATUS_MAP = {
    EntidadNoEncontradaError: 404,
    DuplicadoError: 409,
    CitaSolapadaError: 409,
    CitaEnPasadoError: 422,
    EstadoCitaInvalidoError: 422,
}

@app.exception_handler(DomainError)
async def domain_error_handler(request, exc):
    status_code = EXCEPTION_STATUS_MAP.get(type(exc), 400)
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message},
    )
```

De esta manera, el dominio lanza `CitaSolapadaError` sin saber qué es un código 409, y la presentación lo traduce sin saber por qué se produjo el error. Cada capa se mantiene dentro de los límites de su responsabilidad.

---

## 6. Socialización: desacoplamiento entre capas

El desacoplamiento es la propiedad que permite que cada capa pueda modificarse, reemplazarse o testearse de forma independiente sin afectar a las demás. En este sistema se implementaron cuatro estrategias concretas para lograrlo.

### 6.1. La capa de dominio no depende de frameworks externos

El módulo `app/domain/` únicamente utiliza la librería estándar de Python (módulos `datetime` y `re`). No importa SQLAlchemy, FastAPI ni Pydantic. Esto significa que las reglas de negocio pueden ejecutarse y probarse sin necesidad de levantar un servidor ni conectarse a una base de datos.

Como consecuencia práctica, los tests unitarios del dominio se ejecutan en milisegundos y no requieren ninguna infraestructura.

### 6.2. Inyección de dependencias

Los servicios de la capa de aplicación no crean internamente sus dependencias; las reciben como parámetros en su constructor. El servicio `CitaService` recibe los repositorios de citas, doctores y pacientes al momento de ser instanciado.

Esto permite que en el entorno de producción se inyecten repositorios conectados a una base de datos real, mientras que en los tests se inyecten repositorios conectados a una base de datos en memoria. El código del servicio no cambia en ninguno de los dos casos.

En FastAPI, esta inyección se realiza a través del mecanismo `Depends()`, que resuelve automáticamente las dependencias en cada petición.

### 6.3. Las excepciones del dominio son independientes del protocolo de comunicación

Las excepciones como `CitaSolapadaError` o `EntidadNoEncontradaError` describen errores del negocio sin hacer referencia a HTTP, códigos de estado ni formatos de respuesta. La traducción de estas excepciones a respuestas HTTP se realiza exclusivamente en la capa de presentación, mediante un mapeo centralizado en el módulo `error_handlers.py`.

Si en el futuro se decidiera reemplazar la API REST por una interfaz GraphQL o una interfaz de línea de comandos, las excepciones del dominio seguirían siendo válidas; solo cambiaría la forma de presentarlas al usuario.

### 6.4. Los objetos de transferencia de datos están separados de los modelos de persistencia

El sistema distingue entre los esquemas Pydantic (DTOs) utilizados para la comunicación con el cliente y los modelos SQLAlchemy utilizados para la persistencia. `CitaCreate` y `CitaResponse` son objetos Pydantic que definen qué datos entran y salen de la API, mientras que `CitaModel` es un modelo SQLAlchemy que define cómo se almacenan los datos en la tabla.

Esta separación permite modificar la estructura de la base de datos sin afectar el contrato de la API pública, y viceversa.

---

## 7. Pruebas automatizadas como evidencia del desacoplamiento

El sistema cuenta con una suite de 58 pruebas automatizadas que se dividen en dos categorías:

**Pruebas unitarias (39 tests):** Validan las reglas de negocio y los servicios de forma aislada, sin levantar un servidor HTTP y usando una base de datos SQLite en memoria. Algunos ejemplos:

- Se verifica que no se puede agendar una cita en el pasado.
- Se verifica que se detecta correctamente el solapamiento de horarios.
- Se verifica que no se puede cancelar una cita que ya fue cancelada.
- Se verifica que un email con formato inválido es rechazado.
- Se verifica que registrar un médico con un número de licencia duplicado lanza error.

**Pruebas de integración (19 tests):** Validan el flujo completo desde la petición HTTP hasta la respuesta, pasando por todas las capas. Algunos ejemplos:

- Se verifica que `POST /api/v1/doctores` retorna código 201 al crear un médico.
- Se verifica que `POST /api/v1/citas` con una fecha en el pasado retorna código 422.
- Se verifica que intentar crear una cita solapada retorna código 409.
- Se verifica que `GET /api/v1/doctores/{id}/disponibilidad` retorna los slots correctos.

El hecho de que las pruebas unitarias funcionen sin infraestructura es una consecuencia directa del desacoplamiento: la capa de dominio no depende de nada externo y puede probarse por sí sola.

---

## 8. Estructura del proyecto

```
citas_medicas/
├── app/
│   ├── main.py                         # Punto de entrada de la aplicación
│   ├── config.py                       # Configuración (DB, duración de citas)
│   ├── domain/                         # Capa de Dominio
│   │   ├── entities.py                 #   Entidades: Doctor, Paciente, Cita
│   │   ├── enums.py                    #   Estados de cita y transiciones
│   │   ├── exceptions.py              #   Excepciones de negocio
│   │   └── rules.py                   #   Reglas de negocio puras
│   ├── application/                    # Capa de Aplicación
│   │   ├── schemas.py                  #   DTOs Pydantic (entrada/salida)
│   │   ├── doctor_service.py           #   Casos de uso de doctores
│   │   ├── paciente_service.py         #   Casos de uso de pacientes
│   │   └── cita_service.py            #   Casos de uso de citas
│   ├── infrastructure/                 # Capa de Infraestructura
│   │   ├── database.py                 #   Configuración SQLAlchemy
│   │   ├── models.py                   #   Modelos de base de datos
│   │   └── repositories/              #   Repositorios de acceso a datos
│   │       ├── base.py                 #     Repositorio genérico (CRUD)
│   │       ├── doctor_repo.py          #     Repositorio de doctores
│   │       ├── paciente_repo.py        #     Repositorio de pacientes
│   │       └── cita_repo.py           #     Repositorio de citas
│   └── presentation/                   # Capa de Presentación
│       ├── dependencies.py             #   Inyección de dependencias
│       ├── error_handlers.py           #   Traducción de errores a HTTP
│       └── routers/                    #   Endpoints de la API
│           ├── doctor_router.py        #     Endpoints de doctores
│           ├── paciente_router.py      #     Endpoints de pacientes
│           └── cita_router.py          #     Endpoints de citas
├── tests/                              # Pruebas automatizadas
│   ├── unit/                           #   Pruebas unitarias
│   └── integration/                    #   Pruebas de integración
├── alembic/                            # Migraciones de base de datos
├── Dockerfile                          # Contenedor Docker
├── docker-compose.yml                  # Orquestación Docker
├── pyproject.toml                      # Dependencias del proyecto
└── README.md                           # Documentación técnica
```

---

## 9. Conclusiones

La implementación de este sistema de gestión de citas médicas demuestra que la Arquitectura en Capas es una estrategia efectiva para organizar proyectos de software con complejidad de negocio significativa.

La separación de responsabilidades lograda permite que:

- Las **reglas de negocio** puedan evolucionar sin modificar la API ni la base de datos.
- La **base de datos** pueda cambiarse de SQLite a PostgreSQL modificando únicamente una variable de entorno, sin tocar una sola línea de código en los servicios o en las reglas.
- La **interfaz de comunicación** (actualmente REST) pueda reemplazarse por otra tecnología (GraphQL, gRPC) reescribiendo únicamente la capa de presentación.
- Cada capa pueda **testearse de forma independiente**, lo cual se evidencia en los 58 tests automatizados que cubren tanto la lógica de negocio aislada como el flujo completo del sistema.

El desacoplamiento no es solo un principio teórico: se materializa en decisiones concretas de diseño como la inyección de dependencias, la separación de excepciones de dominio y códigos HTTP, y la distinción entre DTOs y modelos de persistencia.
