from datetime import datetime, timedelta


def _fecha_futura(dias=5, hora=10):
    return (datetime.now() + timedelta(days=dias)).replace(
        hour=hora, minute=0, second=0, microsecond=0
    ).isoformat()


class TestCitaAPI:
    def _crear_doctor_y_paciente(self, client):
        doc = client.post(
            "/api/v1/doctores",
            json={
                "nombre": "Dr. API",
                "especialidad": "General",
                "numero_licencia": "API-001",
            },
        ).json()
        pac = client.post(
            "/api/v1/pacientes",
            json={
                "nombre": "Paciente API",
                "documento": "API-DOC-001",
                "email": "api@test.com",
            },
        ).json()
        return doc["id"], pac["id"]

    def test_agendar_cita(self, client):
        doc_id, pac_id = self._crear_doctor_y_paciente(client)
        response = client.post(
            "/api/v1/citas",
            json={
                "paciente_id": pac_id,
                "doctor_id": doc_id,
                "fecha_hora": _fecha_futura(),
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["estado"] == "PROGRAMADA"
        assert body["duracion_minutos"] == 30

    def test_agendar_cita_en_pasado(self, client):
        doc_id, pac_id = self._crear_doctor_y_paciente(client)
        fecha_pasada = (datetime.now() - timedelta(hours=1)).isoformat()
        response = client.post(
            "/api/v1/citas",
            json={
                "paciente_id": pac_id,
                "doctor_id": doc_id,
                "fecha_hora": fecha_pasada,
            },
        )
        assert response.status_code == 422

    def test_agendar_cita_solapada(self, client):
        doc_id, pac_id = self._crear_doctor_y_paciente(client)
        fecha = _fecha_futura()
        client.post(
            "/api/v1/citas",
            json={
                "paciente_id": pac_id,
                "doctor_id": doc_id,
                "fecha_hora": fecha,
            },
        )
        response = client.post(
            "/api/v1/citas",
            json={
                "paciente_id": pac_id,
                "doctor_id": doc_id,
                "fecha_hora": fecha,
            },
        )
        assert response.status_code == 409

    def test_cancelar_cita(self, client):
        doc_id, pac_id = self._crear_doctor_y_paciente(client)
        cita = client.post(
            "/api/v1/citas",
            json={
                "paciente_id": pac_id,
                "doctor_id": doc_id,
                "fecha_hora": _fecha_futura(),
            },
        ).json()
        response = client.patch(f"/api/v1/citas/{cita['id']}/cancelar")
        assert response.status_code == 200
        assert response.json()["estado"] == "CANCELADA"

    def test_reprogramar_cita(self, client):
        doc_id, pac_id = self._crear_doctor_y_paciente(client)
        cita = client.post(
            "/api/v1/citas",
            json={
                "paciente_id": pac_id,
                "doctor_id": doc_id,
                "fecha_hora": _fecha_futura(dias=5, hora=10),
            },
        ).json()
        response = client.patch(
            f"/api/v1/citas/{cita['id']}/reprogramar",
            json={"nueva_fecha_hora": _fecha_futura(dias=6, hora=14)},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["estado"] == "PROGRAMADA"
        assert body["id"] != cita["id"]

    def test_disponibilidad(self, client):
        doc_id, pac_id = self._crear_doctor_y_paciente(client)
        fecha = _fecha_futura()
        client.post(
            "/api/v1/citas",
            json={
                "paciente_id": pac_id,
                "doctor_id": doc_id,
                "fecha_hora": fecha,
            },
        )
        fecha_str = fecha[:10]
        response = client.get(
            f"/api/v1/doctores/{doc_id}/disponibilidad?fecha={fecha_str}"
        )
        assert response.status_code == 200
        body = response.json()
        assert body["doctor_id"] == doc_id
        assert len(body["slots_disponibles"]) > 0

    def test_citas_por_doctor(self, client):
        doc_id, pac_id = self._crear_doctor_y_paciente(client)
        client.post(
            "/api/v1/citas",
            json={
                "paciente_id": pac_id,
                "doctor_id": doc_id,
                "fecha_hora": _fecha_futura(),
            },
        )
        response = client.get(f"/api/v1/doctores/{doc_id}/citas")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_citas_por_paciente(self, client):
        doc_id, pac_id = self._crear_doctor_y_paciente(client)
        client.post(
            "/api/v1/citas",
            json={
                "paciente_id": pac_id,
                "doctor_id": doc_id,
                "fecha_hora": _fecha_futura(),
            },
        )
        response = client.get(f"/api/v1/pacientes/{pac_id}/citas")
        assert response.status_code == 200
        assert len(response.json()) == 1
