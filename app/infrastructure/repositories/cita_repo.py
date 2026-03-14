from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.enums import EstadoCita
from app.infrastructure.models import CitaModel
from app.infrastructure.repositories.base import BaseRepository


class CitaRepository(BaseRepository[CitaModel]):
    def __init__(self, session: Session):
        super().__init__(session, CitaModel)

    def get_by_doctor(
        self, doctor_id: int, solo_activas: bool = False
    ) -> list[CitaModel]:
        query = self.session.query(CitaModel).filter(
            CitaModel.doctor_id == doctor_id
        )
        if solo_activas:
            query = query.filter(CitaModel.estado == EstadoCita.PROGRAMADA)
        return list(query.all())

    def get_by_paciente(
        self, paciente_id: int, solo_activas: bool = False
    ) -> list[CitaModel]:
        query = self.session.query(CitaModel).filter(
            CitaModel.paciente_id == paciente_id
        )
        if solo_activas:
            query = query.filter(CitaModel.estado == EstadoCita.PROGRAMADA)
        return list(query.all())

    def get_citas_doctor_en_rango(
        self, doctor_id: int, inicio: datetime, fin: datetime
    ) -> list[CitaModel]:
        """Obtiene citas activas del doctor que se solapan con el rango dado."""
        return list(
            self.session.query(CitaModel)
            .filter(
                CitaModel.doctor_id == doctor_id,
                CitaModel.estado == EstadoCita.PROGRAMADA,
                CitaModel.fecha_hora < fin,
            )
            .all()
        )

    def get_citas_doctor_por_fecha(
        self, doctor_id: int, fecha_inicio: datetime, fecha_fin: datetime
    ) -> list[CitaModel]:
        """Obtiene citas activas del doctor en un día específico."""
        return list(
            self.session.query(CitaModel)
            .filter(
                CitaModel.doctor_id == doctor_id,
                CitaModel.estado == EstadoCita.PROGRAMADA,
                CitaModel.fecha_hora >= fecha_inicio,
                CitaModel.fecha_hora < fecha_fin,
            )
            .all()
        )
