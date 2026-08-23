import json
import logging
import os

from kafka import KafkaProducer


logger = logging.getLogger(__name__)

DEFAULT_BOOTSTRAP_SERVERS = "localhost:9092"
DEFAULT_TOPIC = "scenario-jobs"

_producers: dict[str, KafkaProducer] = {}


def get_bootstrap_servers() -> str:
    return os.getenv("KAFKA_BOOTSTRAP_SERVERS", DEFAULT_BOOTSTRAP_SERVERS)


def get_topic() -> str:
    return os.getenv("SCENARIO_JOBS_TOPIC", DEFAULT_TOPIC)


def _get_producer(bootstrap_servers: str) -> KafkaProducer:
    if bootstrap_servers not in _producers:
        _producers[bootstrap_servers] = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            acks=1,
            retries=1,
            request_timeout_ms=10000,
        )
    return _producers[bootstrap_servers]


def publish_scenario_job(job: dict) -> str:
    topic = get_topic()
    payload = json.dumps(job, separators=(",", ":")).encode("utf-8")
    producer = _get_producer(get_bootstrap_servers())
    future = producer.send(topic, key=job["job_id"].encode("utf-8"), value=payload)
    metadata = future.get(timeout=15)
    logger.info(
        "published job_id=%s to %s[%s@%s]",
        job["job_id"],
        metadata.topic,
        metadata.partition,
        metadata.offset,
    )
    return job["job_id"]
