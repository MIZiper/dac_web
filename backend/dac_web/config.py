import logging
import sys
from os import path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    debug: bool = False
    """Enable debug-level logging and verbose error responses."""

    app_log_on: bool = False
    """Capture subprocess stdout/stderr to files on termination."""

    log_dir: str = "./storage/logs"
    """Directory for per-session subprocess log files."""

    dbstore: bool = True
    """Use PostgreSQL (True) or flat JSON files (False) for project storage."""

    postgres_user: str = "postgres"
    postgres_password: str = "password"
    postgres_db: str = "dac"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    keycloak_url: str = ""
    keycloak_url_public: str = ""
    keycloak_realm: str = ""
    keycloak_client_id: str = ""
    keycloak_client_secret: str = ""

    project_dir: str = "./storage/projects"
    """Directory for active project JSON files (file-based storage)."""

    project_save_dir: str = "./storage/projects_save"
    """Directory for published/shared project JSON files (file-based storage)."""

    external_system: str = "tc"
    """External catalog/process system used for resource links (tc or windchill)."""

    external_system_url: str = "http://localhost:8030"
    """Backend base URL of the external system."""

    external_system_ui_url: str = "http://localhost:5130"
    """Browser base URL used to generate external links."""

    external_frozen_statuses: str = "pending_review,published,archived"
    """Comma-separated external statuses that make a linked resource read-only."""

    public_base_url: str = "http://localhost:5131"
    """Browser base URL of this application, used when linking source resources."""

    frontend_dist: str = ""
    """Path to built Svelte frontend. When set, FastAPI serves the SPA."""

    scenario_default: str = "0.base.yaml"
    """Default scenario YAML filename loaded at session startup."""

    scenario_dir: str = ""
    """Directory for scenario YAML files. Falls back to dac package scenarios/."""

    admin_token: str = ""
    """Static admin token for non-Keycloak deployments. Sent as X-Admin-Token header."""

    admin_role: str = "tap:admin"
    """Keycloak realm role name required for admin access."""

    log_buffer_size: int = 2000
    """Number of lines retained in per-session stdout/stderr ring buffers."""

    dac_web_rules_package: str = "dac_web.rules"
    """Python package path for auto-discovering ActionReplacementRule subclasses."""

    @field_validator("keycloak_url_public", mode="after")
    @classmethod
    def _fallback_keycloak_url_public(cls, v: str, info) -> str:
        if not v:
            return info.data.get("keycloak_url", "")
        return v

    @field_validator("scenario_dir", mode="after")
    @classmethod
    def _fallback_scenario_dir(cls, v: str) -> str:
        if not v:
            import dac
            return path.join(path.dirname(dac.__file__), "scenarios")
        return v


settings = Settings()


def setup_logging():
    logger = logging.getLogger("dac_web")
    if settings.debug:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        logger.addHandler(handler)
    else:
        logger.setLevel(logging.WARNING)
    logger.debug("DEBUG mode enabled")
