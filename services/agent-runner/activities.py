import os

from temporalio import activity


INJECT_TRANSIENT_FAILURE_ENV = "INJECT_TRANSIENT_FAILURE_JOB_IDS"


def _injection_ids() -> set[str]:
    raw = os.getenv(INJECT_TRANSIENT_FAILURE_ENV, "")
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
        job.get("job_id") in _injection_ids()
        and activity.info().attempt
        < int(os.getenv("INJECT_TRANSIENT_FAILURE_MAX_ATTEMPTS", "2"))
    ):
        raise RuntimeError(
            f"simulated transient sandbox failure "
            f"(attempt {activity.info().attempt} for job {job.get('job_id')})"
        )
    return {
        "stage": "executed",
        "placeholder": True,
        "sandbox_env": "placeholder-pending-task-3.4",
        "detail": "no real agent or tool executed (Task 3.3 scope)",
        "attempt": activity.info().attempt,
    }


@activity.defn
async def capture_trace(job: dict) -> dict:
    return {
        "stage": "captured",
        "placeholder": True,
        "trace_capturer": "placeholder-pending-task-3.5",
        "detail": "no real trace streamed to Trace Store yet (Task 3.5 scope)",
    }
