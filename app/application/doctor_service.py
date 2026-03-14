from app.application.schemas import DoctorCreate
from app.domain.exceptions import DuplicadoError, EntidadNoEncontradaError
from app.infrastructure.models import DoctorModel
from app.infrastructure.repositories.doctor_repo import DoctorRepository


class DoctorService:
    def __init__(self, repo: DoctorRepository):
        self.repo = repo

    def registrar(self, data: DoctorCreate) -> DoctorModel:
        existente = self.repo.get_by_licencia(data.numero_licencia)
        if existente:
            raise DuplicadoError(
                f"Ya existe un médico con licencia '{data.numero_licencia}'."
            )
        doctor = DoctorModel(
            nombre=data.nombre,
            especialidad=data.especialidad,
            numero_licencia=data.numero_licencia,
        )
        return self.repo.create(doctor)

    def obtener(self, doctor_id: int) -> DoctorModel:
        doctor = self.repo.get_by_id(doctor_id)
        if not doctor:
            raise EntidadNoEncontradaError(
                f"No se encontró el médico con id {doctor_id}."
            )
        return doctor

    def listar(self) -> list[DoctorModel]:
        return self.repo.get_all()
