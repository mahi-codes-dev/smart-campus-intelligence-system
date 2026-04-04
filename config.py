from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _to_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _get_env(name, default=None, *, aliases=None, required=False, cast=str):
    candidates = [name, *(aliases or [])]

    for candidate in candidates:
        value = os.getenv(candidate)
        if value is not None and str(value).strip() != "":
            return cast(value)

    if default is not None:
        return cast(default)

    if required:
        alias_list = ", ".join(candidates)
        raise RuntimeError(f"Missing required environment variable. Expected one of: {alias_list}")

    return None


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    db_host: str | None
    db_name: str | None
    db_user: str | None
    db_password: str | None
    db_port: int
    jwt_secret: str
    jwt_algorithm: str
    jwt_exp_hours: int
    flask_secret_key: str
    flask_env: str
    flask_debug: bool
    app_name: str
    app_url: str


settings = Settings(
    database_url=_get_env("DATABASE_URL"),
    db_host=_get_env("DB_HOST"),
    db_name=_get_env("DB_NAME"),
    db_user=_get_env("DB_USER"),
    db_password=_get_env("DB_PASSWORD"),
    db_port=_get_env("DB_PORT", default="5432", cast=int),
    jwt_secret=_get_env("JWT_SECRET", aliases=["JWT_SECRET_KEY", "SECRET_KEY"], required=True),
    jwt_algorithm=_get_env("JWT_ALGORITHM", default="HS256"),
    jwt_exp_hours=_get_env("JWT_EXP_HOURS", default="24", cast=int),
    flask_secret_key=_get_env("SECRET_KEY", aliases=["JWT_SECRET"], required=True),
    flask_env=_get_env("FLASK_ENV", default="development"),
    flask_debug=_get_env("FLASK_DEBUG", default="true", cast=_to_bool),
    app_name=_get_env("APP_NAME", default="Smart Campus Intelligence System"),
    app_url=_get_env("APP_URL", default="http://localhost:5000"),
)
