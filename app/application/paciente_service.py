from app.application.schemas import PacienteCreate
from app.domain.exceptions import DuplicadoError, EntidadNoEncontradaError
from app.domain.rules import validar_email
from app.infrastructure.models import PacienteModel
from app.infrastructure.repositories.paciente_repo import PacienteRepository


class PacienteService:
    def __init__(self, repo: PacienteRepository):
        self.repo = repo

    def registrar(self, data: PacienteCreate) -> PacienteModel:
        validar_email(data.email)

        existente = self.repo.get_by_documento(data.documento)
        if existente:
            raise DuplicadoError(
                f"Ya existe un paciente con documento '{data.documento}'."
            )
        paciente = PacienteModel(
            nombre=data.nombre,
            documento=data.documento,
            email=data.email,
        )
        return self.repo.create(paciente)

    def obtener(self, paciente_id: int) -> PacienteModel:
        paciente = self.repo.get_by_id(paciente_id)
        if not paciente:
            raise EntidadNoEncontradaError(
                f"No se encontró el paciente con id {paciente_id}."
            )
        return paciente

    def listar(self) -> list[PacienteModel]:
        return self.repo.get_all()
