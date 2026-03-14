import re
from datetime import datetime, timedelta

from app.domain.enums import TRANSICIONES_VALIDAS, EstadoCita
from app.domain.exceptions import (
    CitaEnPasadoError,
    CitaSolapadaError,
    EmailInvalidoError,
    EstadoCitaInvalidoError,
)

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def calcular_fin_cita(inicio: datetime, duracion_minutos: int) -> datetime:
    return inicio + timedelta(minutes=duracion_minutos)


def validar_fecha_futura(fecha: datetime) -> None:
    if fecha <= datetime.now():
        raise CitaEnPasadoError("No se pueden agendar citas en el pasado.")


def validar_no_solapamiento(
    citas_existentes: list[tuple[datetime, int]],
    nueva_fecha: datetime,
    duracion: int,
) -> None:
    """Verifica que la nueva cita no se solape con las existentes.

    citas_existentes: lista de tuplas (fecha_hora_inicio, duracion_minutos)
    """
    nuevo_inicio = nueva_fecha
    nuevo_fin = calcular_fin_cita(nueva_fecha, duracion)

    for inicio_existente, dur_existente in citas_existentes:
        fin_existente = calcular_fin_cita(inicio_existente, dur_existente)
        if nuevo_inicio < fin_existente and nuevo_fin > inicio_existente:
            raise CitaSolapadaError(
                f"El médico ya tiene una cita entre "
                f"{inicio_existente.strftime('%H:%M')} y "
                f"{fin_existente.strftime('%H:%M')}."
            )


def validar_transicion_estado(
    estado_actual: EstadoCita, nuevo_estado: EstadoCita
) -> None:
    estados_permitidos = TRANSICIONES_VALIDAS.get(estado_actual, set())
    if nuevo_estado not in estados_permitidos:
        raise EstadoCitaInvalidoError(
            f"No se puede cambiar de '{estado_actual}' a '{nuevo_estado}'."
        )


def validar_email(email: str) -> None:
    if not EMAIL_REGEX.match(email):
        raise EmailInvalidoError(f"El formato del email '{email}' no es válido.")
