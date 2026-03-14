from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.cita_service import CitaService
from app.application.doctor_service import DoctorService
from app.application.paciente_service import PacienteService
from app.infrastructure.database import SessionLocal
from app.infrastructure.repositories.cita_repo import CitaRepository
from app.infrastructure.repositories.doctor_repo import DoctorRepository
from app.infrastructure.repositories.paciente_repo import PacienteRepository


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


DBSession = Annotated[Session, Depends(get_db)]


def get_doctor_service(db: DBSession) -> DoctorService:
    return DoctorService(DoctorRepository(db))


def get_paciente_service(db: DBSession) -> PacienteService:
    return PacienteService(PacienteRepository(db))


def get_cita_service(db: DBSession) -> CitaService:
    return CitaService(
        cita_repo=CitaRepository(db),
        doctor_repo=DoctorRepository(db),
        paciente_repo=PacienteRepository(db),
    )
