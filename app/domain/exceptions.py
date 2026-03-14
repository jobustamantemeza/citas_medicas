class DomainError(Exception):
    """Excepción base para errores de dominio."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EntidadNoEncontradaError(DomainError):
    """La entidad solicitada no existe."""


class DuplicadoError(DomainError):
    """Ya existe un registro con ese valor único."""


class CitaSolapadaError(DomainError):
    """El médico ya tiene una cita en ese horario."""


class CitaEnPasadoError(DomainError):
    """No se puede agendar una cita en el pasado."""


class EstadoCitaInvalidoError(DomainError):
    """Transición de estado no permitida."""


class EmailInvalidoError(DomainError):
    """El formato del email no es válido."""
