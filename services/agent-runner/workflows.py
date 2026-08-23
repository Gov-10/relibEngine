from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy


with workflow.unsafe.imports_passed_through():
    from activities import capture_trace, execute_in_sandbox, prepare_execution

ACTIVITY_RETRY_POLICY = RetryPolicy(
    maximum_attempts=3,
    initial_interval=timedelta(seconds=1),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=10),
)


@workflow.defn
class ScenarioExecutionWorkflow:
    @workflow.run
    async def run(self, job: dict) -> dict:
        prepared = await workflow.execute_activity(
            prepare_execution,
            job,
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=ACTIVITY_RETRY_POLICY,
        )
        executed = await workflow.execute_activity(
            execute_in_sandbox,
            job,
            start_to_close_timeout=timedelta(seconds=60),
            retry_policy=ACTIVITY_RETRY_POLICY,
        )
        captured = await workflow.execute_activity(
            capture_trace,
            {"job": job, "execution": executed},
            start_to_close_timeout=timedelta(seconds=30),
            retry_policy=ACTIVITY_RETRY_POLICY,
        )
        return {
            "workflow_id": workflow.info().workflow_id,
            "job_id": job.get("job_id"),
            "scenario_id": job.get("scenario_id"),
            "agent_id": job.get("agent_id"),
            "status": "completed",
            "steps": {
                "prepare": prepared,
                "execute": executed,
                "capture": captured,
            },
        }
