from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import (
    CitaEnPasadoError,
    CitaSolapadaError,
    DomainError,
    DuplicadoError,
    EmailInvalidoError,
    EntidadNoEncontradaError,
    EstadoCitaInvalidoError,
)

EXCEPTION_STATUS_MAP: dict[type[DomainError], int] = {
    EntidadNoEncontradaError: 404,
    DuplicadoError: 409,
    CitaSolapadaError: 409,
    CitaEnPasadoError: 422,
    EstadoCitaInvalidoError: 422,
    EmailInvalidoError: 422,
}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        status_code = EXCEPTION_STATUS_MAP.get(type(exc), 400)
        return JSONResponse(
            status_code=status_code,
            content={"detail": exc.message},
        )
