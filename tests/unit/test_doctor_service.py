import pytest

from app.application.doctor_service import DoctorService
from app.application.schemas import DoctorCreate
from app.domain.exceptions import DuplicadoError, EntidadNoEncontradaError
from app.infrastructure.repositories.doctor_repo import DoctorRepository


class TestDoctorService:
    def _get_service(self, db_session):
        return DoctorService(DoctorRepository(db_session))

    def test_registrar_doctor(self, db_session):
        service = self._get_service(db_session)
        data = DoctorCreate(
            nombre="Dr. Test",
            especialidad="General",
            numero_licencia="LIC-001",
        )
        doctor = service.registrar(data)

        assert doctor.id is not None
        assert doctor.nombre == "Dr. Test"
        assert doctor.numero_licencia == "LIC-001"

    def test_registrar_doctor_licencia_duplicada(self, db_session):
        service = self._get_service(db_session)
        data = DoctorCreate(
            nombre="Dr. A",
            especialidad="General",
            numero_licencia="LIC-DUP",
        )
        service.registrar(data)

        data2 = DoctorCreate(
            nombre="Dr. B",
            especialidad="Pediatría",
            numero_licencia="LIC-DUP",
        )
        with pytest.raises(DuplicadoError):
            service.registrar(data2)

    def test_obtener_doctor_existente(self, db_session, doctor_en_db):
        service = self._get_service(db_session)
        doctor = service.obtener(doctor_en_db.id)
        assert doctor.nombre == doctor_en_db.nombre

    def test_obtener_doctor_inexistente(self, db_session):
        service = self._get_service(db_session)
        with pytest.raises(EntidadNoEncontradaError):
            service.obtener(999)

    def test_listar_doctores(self, db_session, doctor_en_db):
        service = self._get_service(db_session)
        doctores = service.listar()
        assert len(doctores) >= 1
