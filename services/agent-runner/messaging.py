import json
import logging
import os

from pydantic import BaseModel, Field, ValidationError


logger = logging.getLogger(__name__)

DEFAULT_BOOTSTRAP_SERVERS = "localhost:9092"
DEFAULT_TOPIC = "scenario-jobs"
DEFAULT_CONSUMER_GROUP = "agent-runner"


def get_bootstrap_servers() -> str:
    return os.getenv("KAFKA_BOOTSTRAP_SERVERS", DEFAULT_BOOTSTRAP_SERVERS)


def get_topic() -> str:
    return os.getenv("SCENARIO_JOBS_TOPIC", DEFAULT_TOPIC)


def get_consumer_group() -> str:
    return os.getenv("KAFKA_CONSUMER_GROUP", DEFAULT_CONSUMER_GROUP)


class ScenarioJob(BaseModel):
    schema_version: int = Field(default=1, ge=1)
    job_id: str = Field(min_length=8, max_length=64)
    scenario_id: int
    agent_id: int
    prompt_id: int | None = None
    agent_name: str | None = None
    severity: str | None = None
    produced_at: str | None = None


class JobValidationError(ValueError):
    pass


def validate_job(raw: object) -> ScenarioJob:
    if not isinstance(raw, dict):
        raise JobValidationError("payload is not a JSON object")
    try:
        return ScenarioJob.model_validate(raw)
    except ValidationError as exc:
        raise JobValidationError(exc.error_count(), exc.errors(include_url=False)) from None


def decode_job(value: bytes) -> ScenarioJob:
    try:
        data = json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise JobValidationError(f"invalid JSON payload: {exc}") from None
    return validate_job(data)
