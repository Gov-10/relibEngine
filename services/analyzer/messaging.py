import json
import logging
import os

from kafka import KafkaProducer


logger = logging.getLogger("analyzer.messaging")

DEFAULT_BOOTSTRAP_SERVERS = "localhost:9092"
DEFAULT_TOPIC = "analysis-events"

_producers: dict[str, KafkaProducer] = {}


def get_bootstrap_servers() -> str:
    return os.getenv("KAFKA_BOOTSTRAP_SERVERS", DEFAULT_BOOTSTRAP_SERVERS)


def get_topic() -> str:
    return os.getenv("ANALYSIS_EVENTS_TOPIC", DEFAULT_TOPIC)


def _get_producer(bootstrap_servers: str) -> KafkaProducer:
    if bootstrap_servers not in _producers:
        _producers[bootstrap_servers] = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            acks=1,
            retries=1,
            request_timeout_ms=10000,
        )
    return _producers[bootstrap_servers]


def publish_analysis_event(event: dict) -> str:
    topic = get_topic()
    payload = json.dumps(event, separators=(",", ":"), default=str).encode("utf-8")
    producer = _get_producer(get_bootstrap_servers())
    future = producer.send(
        topic, key=event["run_id"].encode("utf-8"), value=payload
    )
    metadata = future.get(timeout=15)
    logger.info(
        "published analysis event run_id=%s to %s[%s@%s]",
        event["run_id"],
        metadata.topic,
        metadata.partition,
        metadata.offset,
    )
    return f"{metadata.topic}@{metadata.partition}@{metadata.offset}"
