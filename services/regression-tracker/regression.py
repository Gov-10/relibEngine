"""Deterministic regression computation for one analysis event."""

from collections import Counter


def _failure_delta(previous_types: list[str], current_types: list[str]) -> dict:
    previous_counts = Counter(previous_types)
    current_counts = Counter(current_types)
    delta = {}
    for failure_type in set(previous_counts) | set(current_counts):
        diff = current_counts.get(failure_type, 0) - previous_counts.get(failure_type, 0)
        if diff != 0:
            delta[failure_type] = diff
    return delta


def compute_regression(event, previous) -> dict:
    """Return previous/next linkage for an event given the latest prior result.

    `previous` is the most recent stored RegressionResult row for the same
    agent (may be None for a baseline).
    """
    if previous is None:
        return {
            "previous_run_id": None,
            "previous_score": None,
            "score_delta": None,
            "failure_delta": {},
            "regression_status": "baseline",
        }

    score_delta = event.score - previous.score
    failure_delta = _failure_delta(
        previous.failure_types or [], event.failure_types or []
    )

    if score_delta > 0:
        status = "improved"
    elif score_delta < 0:
        status = "regressed"
    elif previous.passed and not event.passed:
        status = "regressed"
    elif not previous.passed and event.passed:
        status = "improved"
    else:
        status = "unchanged"

    return {
        "previous_run_id": previous.run_id,
        "previous_score": previous.score,
        "score_delta": score_delta,
        "failure_delta": failure_delta,
        "regression_status": status,
    }
