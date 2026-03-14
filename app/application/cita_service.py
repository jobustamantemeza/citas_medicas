from datetime import datetime, time, timedelta

from app.application.schemas import CitaCreate
from app.config import settings
from app.domain.enums import EstadoCita
from app.domain.exceptions import EntidadNoEncontradaError
from app.domain.rules import (
    calcular_fin_cita,
    validar_fecha_futura,
    validar_no_solapamiento,
    validar_transicion_estado,
)
from app.infrastructure.models import CitaModel
from app.infrastructure.repositories.cita_repo import CitaRepository
from app.infrastructure.repositories.doctor_repo import DoctorRepository
from app.infrastructure.repositories.paciente_repo import PacienteRepository


class CitaService:
    def __init__(
        self,
        cita_repo: CitaRepository,
        doctor_repo: DoctorRepository,
        paciente_repo: PacienteRepository,
    ):
        self.cita_repo = cita_repo
        self.doctor_repo = doctor_repo
        self.paciente_repo = paciente_repo
        self.duracion = settings.DURACION_CITA_MINUTOS

    def agendar(self, data: CitaCreate) -> CitaModel:
        doctor = self.doctor_repo.get_by_id(data.doctor_id)
        if not doctor:
            raise EntidadNoEncontradaError(
                f"No se encontró el médico con id {data.doctor_id}."
            )

        paciente = self.paciente_repo.get_by_id(data.paciente_id)
        if not paciente:
            raise EntidadNoEncontradaError(
                f"No se encontró el paciente con id {data.paciente_id}."
            )

        validar_fecha_futura(data.fecha_hora)

        fin_nueva = calcular_fin_cita(data.fecha_hora, self.duracion)
        citas_existentes = self.cita_repo.get_citas_doctor_en_rango(
            data.doctor_id, data.fecha_hora, fin_nueva
        )
        citas_para_validar = [
            (c.fecha_hora, c.duracion_minutos) for c in citas_existentes
        ]
        validar_no_solapamiento(citas_para_validar, data.fecha_hora, self.duracion)

        cita = CitaModel(
            paciente_id=data.paciente_id,
            doctor_id=data.doctor_id,
            fecha_hora=data.fecha_hora,
            duracion_minutos=self.duracion,
            estado=EstadoCita.PROGRAMADA,
        )
        return self.cita_repo.create(cita)

    def cancelar(self, cita_id: int) -> CitaModel:
        cita = self._obtener_cita(cita_id)
        validar_transicion_estado(
            EstadoCita(cita.estado), EstadoCita.CANCELADA
        )
        cita.estado = EstadoCita.CANCELADA
        return self.cita_repo.update(cita)

    def reprogramar(self, cita_id: int, nueva_fecha: datetime) -> CitaModel:
        cita_original = self._obtener_cita(cita_id)
        validar_transicion_estado(
            EstadoCita(cita_original.estado), EstadoCita.REPROGRAMADA
        )

        validar_fecha_futura(nueva_fecha)

        fin_nueva = calcular_fin_cita(nueva_fecha, self.duracion)
        citas_existentes = self.cita_repo.get_citas_doctor_en_rango(
            cita_original.doctor_id, nueva_fecha, fin_nueva
        )
        citas_filtradas = [c for c in citas_existentes if c.id != cita_id]
        citas_para_validar = [
            (c.fecha_hora, c.duracion_minutos) for c in citas_filtradas
        ]
        validar_no_solapamiento(citas_para_validar, nueva_fecha, self.duracion)

        cita_original.estado = EstadoCita.REPROGRAMADA
        self.cita_repo.update(cita_original)

        nueva_cita = CitaModel(
            paciente_id=cita_original.paciente_id,
            doctor_id=cita_original.doctor_id,
            fecha_hora=nueva_fecha,
            duracion_minutos=self.duracion,
            estado=EstadoCita.PROGRAMADA,
        )
        return self.cita_repo.create(nueva_cita)

    def consultar_disponibilidad(
        self, doctor_id: int, fecha: datetime
    ) -> list[dict]:
        doctor = self.doctor_repo.get_by_id(doctor_id)
        if not doctor:
            raise EntidadNoEncontradaError(
                f"No se encontró el médico con id {doctor_id}."
            )

        inicio_dia = fecha.replace(
            hour=settings.HORARIO_INICIO, minute=0, second=0, microsecond=0
        )
        fin_dia = fecha.replace(
            hour=settings.HORARIO_FIN, minute=0, second=0, microsecond=0
        )

        citas_del_dia = self.cita_repo.get_citas_doctor_por_fecha(
            doctor_id, inicio_dia, fin_dia
        )

        ocupados = set()
        for cita in citas_del_dia:
            slot = cita.fecha_hora
            while slot < calcular_fin_cita(cita.fecha_hora, cita.duracion_minutos):
                ocupados.add(slot.time())
                slot += timedelta(minutes=self.duracion)

        slots = []
        current = inicio_dia
        while current < fin_dia:
            if current.time() not in ocupados:
                fin_slot = current + timedelta(minutes=self.duracion)
                slots.append(
                    {"hora_inicio": current.time(), "hora_fin": fin_slot.time()}
                )
            current += timedelta(minutes=self.duracion)

        return slots

    def listar_por_doctor(
        self, doctor_id: int, solo_activas: bool = False
    ) -> list[CitaModel]:
        return self.cita_repo.get_by_doctor(doctor_id, solo_activas)

    def listar_por_paciente(
        self, paciente_id: int, solo_activas: bool = False
    ) -> list[CitaModel]:
        return self.cita_repo.get_by_paciente(paciente_id, solo_activas)

    def _obtener_cita(self, cita_id: int) -> CitaModel:
        cita = self.cita_repo.get_by_id(cita_id)
        if not cita:
            raise EntidadNoEncontradaError(
                f"No se encontró la cita con id {cita_id}."
            )
        return cita
