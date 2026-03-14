from datetime import datetime, timedelta

import pytest

from app.domain.enums import EstadoCita
from app.domain.exceptions import (
    CitaEnPasadoError,
    CitaSolapadaError,
    EmailInvalidoError,
    EstadoCitaInvalidoError,
)
from app.domain.rules import (
    calcular_fin_cita,
    validar_email,
    validar_fecha_futura,
    validar_no_solapamiento,
    validar_transicion_estado,
)


class TestValidarFechaFutura:
    def test_fecha_pasada_lanza_error(self):
        fecha_pasada = datetime.now() - timedelta(hours=1)
        with pytest.raises(CitaEnPasadoError):
            validar_fecha_futura(fecha_pasada)

    def test_fecha_futura_pasa(self):
        fecha_futura = datetime.now() + timedelta(hours=1)
        validar_fecha_futura(fecha_futura)


class TestValidarNoSolapamiento:
    def test_detecta_conflicto(self):
        base = datetime(2026, 3, 15, 10, 0)
        citas_existentes = [(base, 30)]

        with pytest.raises(CitaSolapadaError):
            validar_no_solapamiento(citas_existentes, base, 30)

    def test_detecta_conflicto_parcial(self):
        base = datetime(2026, 3, 15, 10, 0)
        citas_existentes = [(base, 30)]
        nueva = base + timedelta(minutes=15)

        with pytest.raises(CitaSolapadaError):
            validar_no_solapamiento(citas_existentes, nueva, 30)

    def test_sin_conflicto(self):
        base = datetime(2026, 3, 15, 10, 0)
        citas_existentes = [(base, 30)]
        nueva = base + timedelta(minutes=30)

        validar_no_solapamiento(citas_existentes, nueva, 30)

    def test_sin_citas_existentes(self):
        nueva = datetime(2026, 3, 15, 10, 0)
        validar_no_solapamiento([], nueva, 30)


class TestValidarTransicionEstado:
    def test_programada_a_cancelada(self):
        validar_transicion_estado(EstadoCita.PROGRAMADA, EstadoCita.CANCELADA)

    def test_programada_a_completada(self):
        validar_transicion_estado(EstadoCita.PROGRAMADA, EstadoCita.COMPLETADA)

    def test_programada_a_reprogramada(self):
        validar_transicion_estado(
            EstadoCita.PROGRAMADA, EstadoCita.REPROGRAMADA
        )

    def test_cancelada_a_programada_falla(self):
        with pytest.raises(EstadoCitaInvalidoError):
            validar_transicion_estado(
                EstadoCita.CANCELADA, EstadoCita.PROGRAMADA
            )

    def test_completada_a_cancelada_falla(self):
        with pytest.raises(EstadoCitaInvalidoError):
            validar_transicion_estado(
                EstadoCita.COMPLETADA, EstadoCita.CANCELADA
            )

    def test_reprogramada_a_programada_falla(self):
        with pytest.raises(EstadoCitaInvalidoError):
            validar_transicion_estado(
                EstadoCita.REPROGRAMADA, EstadoCita.PROGRAMADA
            )


class TestValidarEmail:
    def test_email_valido(self):
        validar_email("usuario@dominio.com")

    def test_email_sin_arroba(self):
        with pytest.raises(EmailInvalidoError):
            validar_email("usuariodominio.com")

    def test_email_sin_dominio(self):
        with pytest.raises(EmailInvalidoError):
            validar_email("usuario@")

    def test_email_vacio(self):
        with pytest.raises(EmailInvalidoError):
            validar_email("")


class TestCalcularFinCita:
    def test_calculo_correcto(self):
        inicio = datetime(2026, 3, 15, 10, 0)
        fin = calcular_fin_cita(inicio, 30)
        assert fin == datetime(2026, 3, 15, 10, 30)

    def test_calculo_60_minutos(self):
        inicio = datetime(2026, 3, 15, 10, 0)
        fin = calcular_fin_cita(inicio, 60)
        assert fin == datetime(2026, 3, 15, 11, 0)
