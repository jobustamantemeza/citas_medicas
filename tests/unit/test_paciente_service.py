import pytest

from app.application.paciente_service import PacienteService
from app.application.schemas import PacienteCreate
from app.domain.exceptions import DuplicadoError, EntidadNoEncontradaError
from app.infrastructure.repositories.paciente_repo import PacienteRepository


class TestPacienteService:
    def _get_service(self, db_session):
        return PacienteService(PacienteRepository(db_session))

    def test_registrar_paciente(self, db_session):
        service = self._get_service(db_session)
        data = PacienteCreate(
            nombre="Paciente Test",
            documento="DOC-001",
            email="test@email.com",
        )
        paciente = service.registrar(data)

        assert paciente.id is not None
        assert paciente.nombre == "Paciente Test"
        assert paciente.email == "test@email.com"

    def test_registrar_paciente_documento_duplicado(self, db_session):
        service = self._get_service(db_session)
        data = PacienteCreate(
            nombre="Paciente A",
            documento="DOC-DUP",
            email="a@email.com",
        )
        service.registrar(data)

        data2 = PacienteCreate(
            nombre="Paciente B",
            documento="DOC-DUP",
            email="b@email.com",
        )
        with pytest.raises(DuplicadoError):
            service.registrar(data2)

    def test_registrar_paciente_email_invalido(self, db_session):
        service = self._get_service(db_session)
        with pytest.raises(Exception):
            data = PacienteCreate(
                nombre="Paciente X",
                documento="DOC-X",
                email="no-es-email",
            )
            service.registrar(data)

    def test_obtener_paciente_existente(self, db_session, paciente_en_db):
        service = self._get_service(db_session)
        paciente = service.obtener(paciente_en_db.id)
        assert paciente.nombre == paciente_en_db.nombre

    def test_obtener_paciente_inexistente(self, db_session):
        service = self._get_service(db_session)
        with pytest.raises(EntidadNoEncontradaError):
            service.obtener(999)

    def test_listar_pacientes(self, db_session, paciente_en_db):
        service = self._get_service(db_session)
        pacientes = service.listar()
        assert len(pacientes) >= 1
