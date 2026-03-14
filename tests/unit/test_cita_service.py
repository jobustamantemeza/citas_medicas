from datetime import datetime, timedelta

import pytest

from app.application.cita_service import CitaService
from app.application.schemas import CitaCreate
from app.domain.enums import EstadoCita
from app.domain.exceptions import (
    CitaEnPasadoError,
    CitaSolapadaError,
    EntidadNoEncontradaError,
    EstadoCitaInvalidoError,
)
from app.infrastructure.repositories.cita_repo import CitaRepository
from app.infrastructure.repositories.doctor_repo import DoctorRepository
from app.infrastructure.repositories.paciente_repo import PacienteRepository


class TestCitaService:
    def _get_service(self, db_session):
        return CitaService(
            cita_repo=CitaRepository(db_session),
            doctor_repo=DoctorRepository(db_session),
            paciente_repo=PacienteRepository(db_session),
        )

    def _fecha_futura(self, dias=5, hora=10):
        return (datetime.now() + timedelta(days=dias)).replace(
            hour=hora, minute=0, second=0, microsecond=0
        )

    def test_agendar_cita(self, db_session, doctor_en_db, paciente_en_db):
        service = self._get_service(db_session)
        data = CitaCreate(
            paciente_id=paciente_en_db.id,
            doctor_id=doctor_en_db.id,
            fecha_hora=self._fecha_futura(),
        )
        cita = service.agendar(data)

        assert cita.id is not None
        assert cita.estado == EstadoCita.PROGRAMADA
        assert cita.duracion_minutos == 30

    def test_agendar_cita_en_pasado(self, db_session, doctor_en_db, paciente_en_db):
        service = self._get_service(db_session)
        data = CitaCreate(
            paciente_id=paciente_en_db.id,
            doctor_id=doctor_en_db.id,
            fecha_hora=datetime.now() - timedelta(hours=1),
        )
        with pytest.raises(CitaEnPasadoError):
            service.agendar(data)

    def test_agendar_cita_solapada(self, db_session, doctor_en_db, paciente_en_db):
        service = self._get_service(db_session)
        fecha = self._fecha_futura()

        data1 = CitaCreate(
            paciente_id=paciente_en_db.id,
            doctor_id=doctor_en_db.id,
            fecha_hora=fecha,
        )
        service.agendar(data1)

        data2 = CitaCreate(
            paciente_id=paciente_en_db.id,
            doctor_id=doctor_en_db.id,
            fecha_hora=fecha,
        )
        with pytest.raises(CitaSolapadaError):
            service.agendar(data2)

    def test_agendar_doctor_inexistente(self, db_session, paciente_en_db):
        service = self._get_service(db_session)
        data = CitaCreate(
            paciente_id=paciente_en_db.id,
            doctor_id=999,
            fecha_hora=self._fecha_futura(),
        )
        with pytest.raises(EntidadNoEncontradaError):
            service.agendar(data)

    def test_cancelar_cita(self, db_session, doctor_en_db, paciente_en_db):
        service = self._get_service(db_session)
        data = CitaCreate(
            paciente_id=paciente_en_db.id,
            doctor_id=doctor_en_db.id,
            fecha_hora=self._fecha_futura(),
        )
        cita = service.agendar(data)
        cancelada = service.cancelar(cita.id)

        assert cancelada.estado == EstadoCita.CANCELADA

    def test_cancelar_cita_ya_cancelada(self, db_session, doctor_en_db, paciente_en_db):
        service = self._get_service(db_session)
        data = CitaCreate(
            paciente_id=paciente_en_db.id,
            doctor_id=doctor_en_db.id,
            fecha_hora=self._fecha_futura(),
        )
        cita = service.agendar(data)
        service.cancelar(cita.id)

        with pytest.raises(EstadoCitaInvalidoError):
            service.cancelar(cita.id)

    def test_reprogramar_cita(self, db_session, doctor_en_db, paciente_en_db):
        service = self._get_service(db_session)
        data = CitaCreate(
            paciente_id=paciente_en_db.id,
            doctor_id=doctor_en_db.id,
            fecha_hora=self._fecha_futura(dias=5, hora=10),
        )
        cita = service.agendar(data)
        nueva_fecha = self._fecha_futura(dias=6, hora=14)
        nueva_cita = service.reprogramar(cita.id, nueva_fecha)

        assert nueva_cita.estado == EstadoCita.PROGRAMADA
        assert nueva_cita.fecha_hora == nueva_fecha
        assert nueva_cita.id != cita.id

        db_session.refresh(cita)
        assert cita.estado == EstadoCita.REPROGRAMADA

    def test_consultar_disponibilidad(self, db_session, doctor_en_db, paciente_en_db):
        service = self._get_service(db_session)
        fecha = self._fecha_futura()

        data = CitaCreate(
            paciente_id=paciente_en_db.id,
            doctor_id=doctor_en_db.id,
            fecha_hora=fecha,
        )
        service.agendar(data)

        slots = service.consultar_disponibilidad(doctor_en_db.id, fecha)

        horas_ocupadas = [fecha.time()]
        for slot in slots:
            assert slot["hora_inicio"] not in horas_ocupadas

    def test_listar_por_doctor(self, db_session, doctor_en_db, paciente_en_db):
        service = self._get_service(db_session)
        data = CitaCreate(
            paciente_id=paciente_en_db.id,
            doctor_id=doctor_en_db.id,
            fecha_hora=self._fecha_futura(),
        )
        service.agendar(data)

        citas = service.listar_por_doctor(doctor_en_db.id)
        assert len(citas) == 1

    def test_listar_por_doctor_solo_activas(self, db_session, doctor_en_db, paciente_en_db):
        service = self._get_service(db_session)
        data = CitaCreate(
            paciente_id=paciente_en_db.id,
            doctor_id=doctor_en_db.id,
            fecha_hora=self._fecha_futura(),
        )
        cita = service.agendar(data)
        service.cancelar(cita.id)

        activas = service.listar_por_doctor(doctor_en_db.id, solo_activas=True)
        todas = service.listar_por_doctor(doctor_en_db.id, solo_activas=False)

        assert len(activas) == 0
        assert len(todas) == 1
