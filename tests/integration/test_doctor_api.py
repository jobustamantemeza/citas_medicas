class TestDoctorAPI:
    def test_crear_doctor(self, client, doctor_data):
        response = client.post("/api/v1/doctores", json=doctor_data)
        assert response.status_code == 201
        body = response.json()
        assert body["nombre"] == doctor_data["nombre"]
        assert body["numero_licencia"] == doctor_data["numero_licencia"]
        assert "id" in body

    def test_crear_doctor_licencia_duplicada(self, client, doctor_data):
        client.post("/api/v1/doctores", json=doctor_data)
        response = client.post("/api/v1/doctores", json=doctor_data)
        assert response.status_code == 409
        assert "Ya existe" in response.json()["detail"]

    def test_listar_doctores(self, client, doctor_data):
        client.post("/api/v1/doctores", json=doctor_data)
        response = client.get("/api/v1/doctores")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_obtener_doctor(self, client, doctor_data):
        created = client.post("/api/v1/doctores", json=doctor_data).json()
        response = client.get(f"/api/v1/doctores/{created['id']}")
        assert response.status_code == 200
        assert response.json()["nombre"] == doctor_data["nombre"]

    def test_obtener_doctor_inexistente(self, client):
        response = client.get("/api/v1/doctores/999")
        assert response.status_code == 404
