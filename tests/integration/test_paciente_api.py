class TestPacienteAPI:
    def test_crear_paciente(self, client, paciente_data):
        response = client.post("/api/v1/pacientes", json=paciente_data)
        assert response.status_code == 201
        body = response.json()
        assert body["nombre"] == paciente_data["nombre"]
        assert body["documento"] == paciente_data["documento"]

    def test_crear_paciente_documento_duplicado(self, client, paciente_data):
        client.post("/api/v1/pacientes", json=paciente_data)
        response = client.post("/api/v1/pacientes", json=paciente_data)
        assert response.status_code == 409

    def test_crear_paciente_email_invalido(self, client):
        data = {
            "nombre": "Test",
            "documento": "DOC-X",
            "email": "no-es-email",
        }
        response = client.post("/api/v1/pacientes", json=data)
        assert response.status_code == 422

    def test_listar_pacientes(self, client, paciente_data):
        client.post("/api/v1/pacientes", json=paciente_data)
        response = client.get("/api/v1/pacientes")
        assert response.status_code == 200
        assert len(response.json()) >= 1

    def test_obtener_paciente(self, client, paciente_data):
        created = client.post("/api/v1/pacientes", json=paciente_data).json()
        response = client.get(f"/api/v1/pacientes/{created['id']}")
        assert response.status_code == 200

    def test_obtener_paciente_inexistente(self, client):
        response = client.get("/api/v1/pacientes/999")
        assert response.status_code == 404
