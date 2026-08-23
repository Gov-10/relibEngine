import json
import logging

from pydantic import ValidationError

from schemas import AnalysisEvent


logger = logging.getLogger("scorecard.messaging")


def decode_event(value: bytes) -> AnalysisEvent:
    """Deserialize and validate one analysis-events message."""
    try:
        data = json.loads(value.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON payload: {exc}") from None
    if not isinstance(data, dict):
        raise ValueError("payload is not a JSON object")
    try:
        return AnalysisEvent.model_validate(data)
    except ValidationError as exc:
        raise ValueError(
            f"{exc.error_count()} validation error(s): "
            f"{exc.errors(include_url=False)[:3]}"
        ) from None
