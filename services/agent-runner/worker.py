import asyncio
import logging
import os
import signal
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from temporalio.client import Client
from temporalio.worker import Worker

from activities import capture_trace, execute_in_sandbox, prepare_execution
from workflows import ScenarioExecutionWorkflow


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("agent-runner.worker")


def get_temporal_address() -> str:
    return os.getenv("TEMPORAL_ADDRESS", "localhost:7233")


def get_temporal_namespace() -> str:
    return os.getenv("TEMPORAL_NAMESPACE", "relib-engine")


def get_task_queue() -> str:
    return os.getenv("TEMPORAL_TASK_QUEUE", "scenario-execution")


async def main() -> None:
    address = get_temporal_address()
    namespace = get_temporal_namespace()
    task_queue = get_task_queue()
    client = await Client.connect(address, namespace=namespace)
    worker = Worker(
        client,
        task_queue=task_queue,
        workflows=[ScenarioExecutionWorkflow],
        activities=[prepare_execution, execute_in_sandbox, capture_trace],
        max_concurrent_activities=10,
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    logger.info(
        'worker started {"task_queue": "%s", "temporal": "%s/%s"}',
        task_queue,
        address,
        namespace,
    )
    async with worker:
        await stop_event.wait()
    logger.info("worker stopped cleanly")


if __name__ == "__main__":
    asyncio.run(main())
