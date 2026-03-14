from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.database import create_tables
from app.presentation.error_handlers import register_error_handlers
from app.presentation.routers import cita_router, doctor_router, paciente_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="Sistema de Gestión de Citas Médicas",
    description="API REST para gestionar médicos, pacientes y citas médicas.",
    version="0.1.0",
    lifespan=lifespan,
)

register_error_handlers(app)

app.include_router(doctor_router.router)
app.include_router(paciente_router.router)
app.include_router(cita_router.router)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
