from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.application.paciente_service import PacienteService
from app.application.schemas import PacienteCreate, PacienteResponse
from app.presentation.dependencies import get_paciente_service

router = APIRouter(prefix="/api/v1/pacientes", tags=["Pacientes"])

PacienteServiceDep = Annotated[PacienteService, Depends(get_paciente_service)]


@router.post(
    "",
    response_model=PacienteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un paciente",
)
def crear_paciente(data: PacienteCreate, service: PacienteServiceDep):
    return service.registrar(data)


@router.get(
    "",
    response_model=list[PacienteResponse],
    summary="Listar todos los pacientes",
)
def listar_pacientes(service: PacienteServiceDep):
    return service.listar()


@router.get(
    "/{paciente_id}",
    response_model=PacienteResponse,
    summary="Obtener un paciente por ID",
)
def obtener_paciente(paciente_id: int, service: PacienteServiceDep):
    return service.obtener(paciente_id)
