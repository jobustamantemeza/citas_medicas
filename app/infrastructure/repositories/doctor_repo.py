from sqlalchemy.orm import Session

from app.infrastructure.models import DoctorModel
from app.infrastructure.repositories.base import BaseRepository


class DoctorRepository(BaseRepository[DoctorModel]):
    def __init__(self, session: Session):
        super().__init__(session, DoctorModel)

    def get_by_licencia(self, numero_licencia: str) -> DoctorModel | None:
        return (
            self.session.query(DoctorModel)
            .filter(DoctorModel.numero_licencia == numero_licencia)
            .first()
        )
