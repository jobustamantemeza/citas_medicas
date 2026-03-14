import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database import Base
from app.infrastructure.models import CitaModel, DoctorModel, PacienteModel
from app.main import app
from app.presentation.dependencies import get_db

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(setup_database):
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    from starlette.testclient import TestClient

    def override_get_db():
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def doctor_data():
    return {
        "nombre": "Dr. García",
        "especialidad": "Cardiología",
        "numero_licencia": "MED-001",
    }


@pytest.fixture
def paciente_data():
    return {
        "nombre": "Juan Pérez",
        "documento": "DNI-123456",
        "email": "juan@email.com",
    }


@pytest.fixture
def doctor_en_db(db_session):
    doctor = DoctorModel(
        nombre="Dra. López",
        especialidad="Pediatría",
        numero_licencia="MED-100",
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(doctor)
    return doctor


@pytest.fixture
def paciente_en_db(db_session):
    paciente = PacienteModel(
        nombre="Ana Torres",
        documento="DNI-999999",
        email="ana@email.com",
    )
    db_session.add(paciente)
    db_session.commit()
    db_session.refresh(paciente)
    return paciente
