"""Trace Capturer component (inside Agent Runner).

Persists structured Sandbox execution results into the existing Trace Store
(models.Run / models.TraceStep). One run row per execution plus one
trace_step row per tool call, preserving order via step_index.

Idempotency: trace_id is deterministically derived from the job id
(trace-<job_id>) which carries a UNIQUE constraint, so Temporal retries of
this capture step never create duplicate records.

Boundary: this component ONLY writes traces to Trace Store. It does not
classify failures, compute scores, or publish to any queue.
"""

import logging
import os
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from models import Run, TraceStep


logger = logging.getLogger("agent-runner.trace-capturer")

INJECT_CAPTURE_FAILURE_ENV = "INJECT_CAPTURE_FAILURE_JOB_IDS"

ALLOWED_RUN_STATUSES = {"completed", "failed", "timeout", "cancelled", "running"}


def _injection_ids() -> set[str]:
    raw = os.getenv(INJECT_CAPTURE_FAILURE_ENV, "")
    return {part.strip() for part in raw.split(",") if part.strip()}


def trace_id_for_job(job_id: str | None) -> str:
    return f"trace-{job_id}"


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _build_run_fields(job: dict, execution: dict, workflow_id: str | None) -> dict:
    status = execution.get("status", "completed")
    if status not in ALLOWED_RUN_STATUSES:
        status = "completed"
    sandbox_info = execution.get("sandbox", {})
    return {
        "run_id": execution["run_id"],
        "trace_id": trace_id_for_job(job.get("job_id")),
        "scenario_ref": (
            str(job["scenario_id"]) if job.get("scenario_id") is not None else None
        ),
        "temporal_workflow_id": workflow_id,
        "agent_name": job.get("agent_name"),
        "status": status,
        "total_latency_ms": execution.get("duration_ms"),
        "llm_call_count": 0,
        "tool_call_count": len(execution.get("tool_calls", [])),
        "metadata_json": {
            "job_id": job.get("job_id"),
            "severity": job.get("severity"),
            "expected_behavior": job.get("expected_behavior"),
            "mock_agent": execution.get("mock_agent"),
            "user_text_preview": execution.get("user_text_preview"),
            "sandbox_type": sandbox_info.get("type"),
            "external_calls_made": sandbox_info.get("external_calls_made"),
            "tools_available": sandbox_info.get("tools_available"),
            "final_state": sandbox_info.get("final_state"),
            "attempted_destructive_actions": execution.get(
                "attempted_destructive_actions", []
            ),
        },
        "started_at": _parse_ts(execution.get("started_at")),
        "finished_at": _parse_ts(execution.get("finished_at")),
    }


def _build_step(index: int, call: dict) -> TraceStep:
    output_data: dict = {}
    if "result" in call:
        output_data["result"] = call["result"]
    output_data["destructive"] = bool(call.get("destructive"))
    failed = call.get("status") == "error"
    return TraceStep(
        step_index=index,
        span_id=f"span-{index:04d}",
        parent_span_id=None,
        step_type="tool_call",
        tool_name=call.get("tool"),
        input_data={"arguments": call.get("arguments")},
        output_data=output_data,
        error_text=call.get("error"),
        latency_ms=float(call.get("latency_ms") or 0.0),
        # Raw error recording only: 'other' is the neutral bucket so the
        # Analyzer (Task 4.1) performs all real failure classification.
        failure_flag=failed,
        failure_type="other" if failed else None,
    )


def capture_report(
    persisted: bool,
    *,
    idempotent_replay: bool = False,
    runs_written: int = 0,
    steps_written: int = 0,
    trace_id: str | None = None,
    run_id: str | None = None,
    error: str | None = None,
) -> dict:
    return {
        "persisted": persisted,
        "idempotent_replay": idempotent_replay,
        "runs_written": runs_written,
        "steps_written": steps_written,
        "trace_id": trace_id,
        "run_id": run_id,
        "error": error,
    }


def _replay_report(session, trace_id: str) -> dict:
    existing = session.query(Run).filter(Run.trace_id == trace_id).one_or_none()
    if existing is None:
        return capture_report(False, error="replay check failed: run vanished")
    steps = session.query(TraceStep).filter(TraceStep.run_id == existing.id).count()
    logger.info(
        "trace %s already captured (run_id=%s, %s steps); skipping duplicates",
        trace_id,
        existing.run_id,
        steps,
    )
    return capture_report(
        True,
        idempotent_replay=True,
        trace_id=trace_id,
        run_id=existing.run_id,
        steps_written=steps,
    )


def capture_trace_execution(
    job: dict,
    execution: dict,
    workflow_id: str | None = None,
    force_failure: bool = False,
) -> dict:
    """Persist one sandbox execution into Trace Store. Never raises."""
    job_id = job.get("job_id")
    trace_id = trace_id_for_job(job_id)

    if force_failure or job_id in _injection_ids():
        error = f"simulated trace-store outage (injected for {job_id})"
        logger.warning("capture failed for %s: %s", trace_id, error)
        return capture_report(False, error=error)

    session = SessionLocal()
    try:
        existing = session.query(Run).filter(Run.trace_id == trace_id).one_or_none()
        if existing is not None:
            session.close()
            return _replay_report(SessionLocal(), trace_id)

        calls = execution.get("tool_calls", [])
        run = Run(**_build_run_fields(job, execution, workflow_id))
        session.add(run)
        session.flush()
        for index, call in enumerate(calls, start=1):
            step = _build_step(index, call)
            step.run_id = run.id
            session.add(step)
        session.commit()
        logger.info(
            'captured {"trace_id": "%s", "run_id": "%s", "steps": %d}',
            trace_id,
            execution["run_id"],
            len(calls),
        )
        return capture_report(
            True,
            runs_written=1,
            steps_written=len(calls),
            trace_id=trace_id,
            run_id=execution["run_id"],
        )
    except IntegrityError as exc:
        session.rollback()
        logger.warning(
            "concurrent capture detected for %s (%s); treating as idempotent replay",
            trace_id,
            str(exc).split("\n")[0][:200],
        )
        return _replay_report(SessionLocal(), trace_id)
    except Exception as exc:
        session.rollback()
        error = f"{type(exc).__name__}: {exc}"[:300]
        logger.exception("trace capture FAILED for %s: %s", trace_id, error)
        return capture_report(False, error=error)
    finally:
        session.close()
