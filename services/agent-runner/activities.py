import os

from temporalio import activity

import sandbox
import trace_capturer


INJECT_TRANSIENT_FAILURE_ENV = "INJECT_TRANSIENT_FAILURE_JOB_IDS"
INJECT_CAPTURE_FAILURE_ENV = "INJECT_CAPTURE_FAILURE_JOB_IDS"


def _injection_ids(env_name: str) -> set[str]:
    raw = os.getenv(env_name, "")
    return {part.strip() for part in raw.split(",") if part.strip()}


@activity.defn
async def prepare_execution(job: dict) -> dict:
    return {
        "stage": "prepared",
        "placeholder": True,
        "detail": f"execution plan ready for scenario {job.get('scenario_id')}",
        "attempt": activity.info().attempt,
    }


@activity.defn
async def execute_in_sandbox(job: dict) -> dict:
    if (
        job.get("job_id") in _injection_ids(INJECT_TRANSIENT_FAILURE_ENV)
        and activity.info().attempt
        < int(os.getenv("INJECT_TRANSIENT_FAILURE_MAX_ATTEMPTS", "2"))
    ):
        raise RuntimeError(
            f"simulated transient sandbox failure "
            f"(attempt {activity.info().attempt} for job {job.get('job_id')})"
        )
    result = sandbox.run_in_sandbox(job)
    result["stage"] = "executed"
    result["attempt"] = activity.info().attempt
    return result


@activity.defn
async def capture_trace(payload: dict) -> dict:
    job = payload.get("job") or {}
    execution = payload.get("execution") or {}
    report = trace_capturer.capture_trace_execution(
        job,
        execution,
        workflow_id=activity.info().workflow_id,
        force_failure=job.get("job_id") in _injection_ids(INJECT_CAPTURE_FAILURE_ENV),
    )
    return {
        "stage": "captured",
        "capture": report,
        "attempt": activity.info().attempt,
    }
