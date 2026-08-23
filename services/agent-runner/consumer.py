"""Standalone Kafka consumer for scenario-jobs (Agent Runner).

Each valid ScenarioJob starts a Temporal workflow
(scenario-exec-<job_id>) on the scenario-execution task queue.
Kafka offsets are committed only after the workflow start succeeds.

Run:  python consumer.py
Env:  KAFKA_BOOTSTRAP_SERVERS (default localhost:9092)
      SCENARIO_JOBS_TOPIC     (default scenario-jobs)
      KAFKA_CONSUMER_GROUP    (default agent-runner)
      TEMPORAL_ADDRESS        (default localhost:7233)
      TEMPORAL_NAMESPACE      (default relib-engine)
      TEMPORAL_TASK_QUEUE     (default scenario-execution)
"""

import logging
import os
import signal
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from messaging import (
    JobValidationError,
    ScenarioJob,
    decode_job,
    get_bootstrap_servers,
    get_consumer_group,
    get_topic,
)
from temporal_starter import (
    TemporalStarter,
    TemporalWorkflowStartError,
    WorkflowAlreadyRunning,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("agent-runner.consumer")

RETRY_BACKOFF_SECONDS = 30
POLL_TIMEOUT_MS = 500

_stop = threading.Event()


def _handle_signal(signum, _frame):
    logger.info("shutdown requested (signal %s)", signum)
    _stop.set()


def process_message(raw: bytes, starter: TemporalStarter) -> bool:
    try:
        job = decode_job(raw)
    except JobValidationError as exc:
        logger.warning("skipping invalid message (%s)", exc)
        return True

    try:
        started = starter.start_workflow_sync(job.model_dump())
    except WorkflowAlreadyRunning:
        logger.info(
            "job %s already has a running/completed workflow; acknowledging", job.job_id
        )
        return True
    except TemporalWorkflowStartError as exc:
        logger.warning(
            "temporal start failed for job %s (%s); will redeliver", job.job_id, exc
        )
        return False

    logger.info(
        'ACK {"job_id": "%s", "scenario_id": %s, "agent_id": %s, '
        '"workflow_id": "%s", "started": %s}',
        job.job_id,
        job.scenario_id,
        job.agent_id,
        starter.workflow_id_for_job(job.job_id),
        str(started is not None).lower(),
    )
    return True


def run_consumer() -> None:
    bootstrap = get_bootstrap_servers()
    topic = get_topic()
    group = get_consumer_group()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handle_signal)
        except ValueError:
            pass

    starter = TemporalStarter()
    if not starter.start():
        logger.warning("continuing without temporal; messages will be redelivered")

    backoff = 1
    consumer = None
    while not _stop.is_set():
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=bootstrap,
                group_id=group,
                auto_offset_reset="earliest",
                enable_auto_commit=False,
            )
        except KafkaError as exc:
            logger.warning(
                "kafka unavailable at %s (%s); retrying in %ss", bootstrap, exc, backoff
            )
            _stop.wait(backoff)
            backoff = min(RETRY_BACKOFF_SECONDS, backoff * 2)
            continue

        backoff = 1
        logger.info("consumer up: topic=%s group=%s bootstrap=%s", topic, group, bootstrap)
        try:
            while not _stop.is_set():
                batches = consumer.poll(timeout_ms=POLL_TIMEOUT_MS)
                for records in batches.values():
                    for message in records:
                        if process_message(message.value, starter):
                            consumer.commit()
        except KafkaError as exc:
            logger.warning("kafka error during consumption (%s); reconnecting", exc)
            consumer.close()
            time.sleep(2)
            continue
        finally:
            if consumer is not None:
                try:
                    consumer.close()
                except Exception:
                    pass
        break

    starter.shutdown()
    logger.info("consumer stopped cleanly")


if __name__ == "__main__":
    run_consumer()
