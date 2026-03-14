from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./citas_medicas.db"
    DURACION_CITA_MINUTOS: int = 30
    HORARIO_INICIO: int = 8
    HORARIO_FIN: int = 18

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
