from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import EstadoCita


@dataclass
class Doctor:
    nombre: str
    especialidad: str
    numero_licencia: str
    id: int | None = None


@dataclass
class Paciente:
    nombre: str
    documento: str
    email: str
    id: int | None = None


@dataclass
class Cita:
    paciente_id: int
    doctor_id: int
    fecha_hora: datetime
    duracion_minutos: int
    estado: EstadoCita = field(default=EstadoCita.PROGRAMADA)
    id: int | None = None
