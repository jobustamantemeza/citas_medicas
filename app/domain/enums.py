from enum import StrEnum


class EstadoCita(StrEnum):
    PROGRAMADA = "PROGRAMADA"
    COMPLETADA = "COMPLETADA"
    CANCELADA = "CANCELADA"
    REPROGRAMADA = "REPROGRAMADA"


TRANSICIONES_VALIDAS: dict[EstadoCita, set[EstadoCita]] = {
    EstadoCita.PROGRAMADA: {
        EstadoCita.COMPLETADA,
        EstadoCita.CANCELADA,
        EstadoCita.REPROGRAMADA,
    },
    EstadoCita.COMPLETADA: set(),
    EstadoCita.CANCELADA: set(),
    EstadoCita.REPROGRAMADA: set(),
}
