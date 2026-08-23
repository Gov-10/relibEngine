import asyncio
import logging
import os
import threading

from temporalio.client import Client
from temporalio.exceptions import WorkflowAlreadyStartedError
from temporalio.service import RPCError


logger = logging.getLogger("agent-runner.temporal-starter")


def get_temporal_address() -> str:
    return os.getenv("TEMPORAL_ADDRESS", "localhost:7233")


def get_temporal_namespace() -> str:
    return os.getenv("TEMPORAL_NAMESPACE", "relib-engine")


def get_task_queue() -> str:
    return os.getenv("TEMPORAL_TASK_QUEUE", "scenario-execution")


class TemporalWorkflowStartError(RuntimeError):
    pass


class WorkflowAlreadyRunning(Exception):
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        super().__init__(f"workflow already running/completed: {workflow_id}")


class TemporalStarter:
    """Bridges the sync Kafka consumer loop to the async temporalio client."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._client: Client | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._stopped = threading.Event()
        self._stop_async_event: asyncio.Event | None = None
        self._connect_error: str | None = None

    def start(self, connect_timeout_s: float = 30.0) -> bool:
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="temporal-starter"
        )
        self._thread.start()
        if not self._ready.wait(timeout=connect_timeout_s):
            return False
        if self._client is None:
            logger.warning(
                "temporal client not connected at %s (%s)",
                get_temporal_address(),
                self._connect_error,
            )
            return False
        logger.info(
            'temporal connected {"address": "%s", "namespace": "%s"}',
            get_temporal_address(),
            get_temporal_namespace(),
        )
        return True

    def _run_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect_and_hold())
        finally:
            self._loop.close()

    async def _connect_and_hold(self) -> None:
        backoff = 1.0
        while not self._stopped.is_set():
            try:
                self._client = await Client.connect(
                    get_temporal_address(),
                    namespace=get_temporal_namespace(),
                )
                break
            except Exception as exc:
                self._connect_error = str(exc)[:200]
                logger.warning(
                    "temporal connect failed (%s); retrying in %.0fs",
                    self._connect_error,
                    backoff,
                )
                await asyncio.sleep(backoff)
                backoff = min(30.0, backoff * 2)
        self._ready.set()
        if self._client is not None:
            self._stop_async_event = asyncio.Event()
            await self._stop_async_event.wait()

    @staticmethod
    def workflow_id_for_job(job_id: str) -> str:
        return f"scenario-exec-{job_id}"

    def start_workflow_sync(self, job: dict, timeout_s: float = 20.0) -> str:
        if self._loop is None or self._client is None or not self._ready.is_set():
            raise TemporalWorkflowStartError("temporal client unavailable")
        future = asyncio.run_coroutine_threadsafe(self._start_workflow(job), self._loop)
        try:
            return future.result(timeout=timeout_s)
        except TimeoutError:
            raise TemporalWorkflowStartError("workflow start timed out")

    async def _start_workflow(self, job: dict) -> str:
        workflow_id = self.workflow_id_for_job(job["job_id"])
        try:
            handle = await self._client.start_workflow(
                "ScenarioExecutionWorkflow",
                job,
                id=workflow_id,
                task_queue=get_task_queue(),
            )
        except WorkflowAlreadyStartedError:
            logger.info(
                "workflow %s already started previously; treating as success",
                workflow_id,
            )
            raise WorkflowAlreadyRunning(workflow_id) from None
        except RPCError as exc:
            raise TemporalWorkflowStartError(f"{type(exc).__name__}: {exc}") from exc
        logger.info(
            'workflow started {"workflow_id": "%s", "run_id": "%s", '
            '"job_id": "%s", "scenario_id": %s}',
            workflow_id,
            handle.first_execution_run_id,
            job.get("job_id"),
            job.get("scenario_id"),
        )
        return workflow_id

    def shutdown(self) -> None:
        self._stopped.set()
        if self._loop is not None and self._stop_async_event is not None:
            self._loop.call_soon_threadsafe(self._stop_async_event.set)
        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=10)
        logger.info("temporal starter stopped")
