from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, EmailStr


class DoctorCreate(BaseModel):
    nombre: str
    especialidad: str
    numero_licencia: str


class DoctorResponse(BaseModel):
    id: int
    nombre: str
    especialidad: str
    numero_licencia: str

    model_config = ConfigDict(from_attributes=True)


class PacienteCreate(BaseModel):
    nombre: str
    documento: str
    email: EmailStr


class PacienteResponse(BaseModel):
    id: int
    nombre: str
    documento: str
    email: str

    model_config = ConfigDict(from_attributes=True)


class CitaCreate(BaseModel):
    paciente_id: int
    doctor_id: int
    fecha_hora: datetime


class CitaReprogramar(BaseModel):
    nueva_fecha_hora: datetime


class CitaResponse(BaseModel):
    id: int
    paciente_id: int
    doctor_id: int
    fecha_hora: datetime
    duracion_minutos: int
    estado: str

    model_config = ConfigDict(from_attributes=True)


class SlotDisponible(BaseModel):
    hora_inicio: time
    hora_fin: time


class DisponibilidadResponse(BaseModel):
    doctor_id: int
    fecha: str
    slots_disponibles: list[SlotDisponible]
