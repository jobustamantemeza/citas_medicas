from sqlalchemy.orm import Session

from app.infrastructure.models import PacienteModel
from app.infrastructure.repositories.base import BaseRepository


class PacienteRepository(BaseRepository[PacienteModel]):
    def __init__(self, session: Session):
        super().__init__(session, PacienteModel)

    def get_by_documento(self, documento: str) -> PacienteModel | None:
        return (
            self.session.query(PacienteModel)
            .filter(PacienteModel.documento == documento)
            .first()
        )
