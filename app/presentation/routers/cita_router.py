from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.application.cita_service import CitaService
from app.application.schemas import (
    CitaCreate,
    CitaReprogramar,
    CitaResponse,
    DisponibilidadResponse,
    SlotDisponible,
)
from app.presentation.dependencies import get_cita_service

router = APIRouter(prefix="/api/v1", tags=["Citas"])

CitaServiceDep = Annotated[CitaService, Depends(get_cita_service)]


@router.post(
    "/citas",
    response_model=CitaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agendar una cita",
)
def agendar_cita(data: CitaCreate, service: CitaServiceDep):
    return service.agendar(data)


@router.patch(
    "/citas/{cita_id}/cancelar",
    response_model=CitaResponse,
    summary="Cancelar una cita",
)
def cancelar_cita(cita_id: int, service: CitaServiceDep):
    return service.cancelar(cita_id)


@router.patch(
    "/citas/{cita_id}/reprogramar",
    response_model=CitaResponse,
    summary="Reprogramar una cita",
)
def reprogramar_cita(
    cita_id: int, data: CitaReprogramar, service: CitaServiceDep
):
    return service.reprogramar(cita_id, data.nueva_fecha_hora)


@router.get(
    "/doctores/{doctor_id}/disponibilidad",
    response_model=DisponibilidadResponse,
    summary="Consultar disponibilidad de un médico",
)
def consultar_disponibilidad(
    doctor_id: int,
    fecha: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    service: CitaServiceDep = None,
):
    fecha_dt = datetime.strptime(fecha, "%Y-%m-%d")
    slots = service.consultar_disponibilidad(doctor_id, fecha_dt)
    slots_response = [
        SlotDisponible(hora_inicio=s["hora_inicio"], hora_fin=s["hora_fin"])
        for s in slots
    ]
    return DisponibilidadResponse(
        doctor_id=doctor_id,
        fecha=fecha,
        slots_disponibles=slots_response,
    )


@router.get(
    "/doctores/{doctor_id}/citas",
    response_model=list[CitaResponse],
    summary="Listar citas de un médico",
)
def listar_citas_doctor(
    doctor_id: int,
    activas: bool = Query(False, description="Solo mostrar citas activas"),
    service: CitaServiceDep = None,
):
    return service.listar_por_doctor(doctor_id, solo_activas=activas)


@router.get(
    "/pacientes/{paciente_id}/citas",
    response_model=list[CitaResponse],
    summary="Listar citas de un paciente",
)
def listar_citas_paciente(
    paciente_id: int,
    activas: bool = Query(False, description="Solo mostrar citas activas"),
    service: CitaServiceDep = None,
):
    return service.listar_por_paciente(paciente_id, solo_activas=activas)
