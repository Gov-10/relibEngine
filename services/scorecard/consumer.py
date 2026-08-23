"""Standalone background consumer for analysis-events (Scorecard Service).

Run:  python consumer.py
Env:  KAFKA_BOOTSTRAP_SERVERS (default localhost:9092)
      ANALYSIS_EVENTS_TOPIC   (default analysis-events)
      KAFKA_CONSUMER_GROUP    (default scorecard-service)
      SCORECARD_SERVER_URL / SCORECARD_DB_NAME / SCORECARD_DATABASE_URL
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

from messaging import decode_event
import store


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("scorecard.consumer")

RETRY_BACKOFF_SECONDS = 30


def get_bootstrap_servers() -> str:
    return os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


def get_topic() -> str:
    return os.getenv("ANALYSIS_EVENTS_TOPIC", "analysis-events")


def get_consumer_group() -> str:
    return os.getenv("KAFKA_CONSUMER_GROUP", "scorecard-service")


_stop = threading.Event()


def _handle_signal(signum, _frame):
    logger.info("shutdown requested (signal %s)", signum)
    _stop.set()


def process_message(raw: bytes) -> bool:
    try:
        event = decode_event(raw)
    except ValueError as exc:
        logger.warning("skipping invalid message (%s)", exc)
        return True
    report = store.persist_analysis_event(event)
    if report.get("error"):
        logger.warning("persistence problem for %s: %s", event.run_id, report["error"])
        return False
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

    store.init()
    logger.info("scorecard store ready")

    backoff = 1
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
                batches = consumer.poll(timeout_ms=500)
                for records in batches.values():
                    for message in records:
                        if process_message(message.value):
                            consumer.commit()
        except KeyboardInterrupt:
            break
        except KafkaError as exc:
            logger.warning("kafka error during consumption (%s); reconnecting", exc)
            time.sleep(2)
            continue
        finally:
            try:
                consumer.close()
            except Exception:
                pass
        break

    logger.info("scorecard consumer stopped cleanly")


if __name__ == "__main__":
    run_consumer()
