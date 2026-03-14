from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.application.doctor_service import DoctorService
from app.application.schemas import DoctorCreate, DoctorResponse
from app.presentation.dependencies import get_doctor_service

router = APIRouter(prefix="/api/v1/doctores", tags=["Doctores"])

DoctorServiceDep = Annotated[DoctorService, Depends(get_doctor_service)]


@router.post(
    "",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un médico",
)
def crear_doctor(data: DoctorCreate, service: DoctorServiceDep):
    return service.registrar(data)


@router.get(
    "",
    response_model=list[DoctorResponse],
    summary="Listar todos los médicos",
)
def listar_doctores(service: DoctorServiceDep):
    return service.listar()


@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Obtener un médico por ID",
)
def obtener_doctor(doctor_id: int, service: DoctorServiceDep):
    return service.obtener(doctor_id)
