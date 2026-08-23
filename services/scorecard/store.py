import logging

from sqlalchemy.exc import IntegrityError

from database import ensure_database, get_engine, get_session_factory
from models import Base, Scorecard


logger = logging.getLogger("scorecard.store")


def init() -> None:
    ensure_database()
    Base.metadata.create_all(get_engine(), checkfirst=True)


def event_key_for(run_id: str, analyzed_at: str) -> str:
    return f"{run_id}:{analyzed_at}"


def persist_analysis_event(event) -> dict:
    """Store one point-in-time scorecard. Idempotent per (run_id, analyzed_at)."""
    session = get_session_factory()()
    try:
        key = event_key_for(event.run_id, event.analyzed_at)
        existing = (
            session.query(Scorecard)
            .filter(Scorecard.event_key == key)
            .one_or_none()
        )
        if existing is not None:
            logger.info("duplicate analysis event %s; ignoring replay", key)
            return {
                "stored": False,
                "idempotent_replay": True,
                "event_key": key,
                "scorecard_id": existing.id,
            }
        row = Scorecard(
            event_key=key,
            run_id=event.run_id,
            trace_id=event.trace_id,
            scenario_ref=event.scenario_ref,
            agent_name=event.agent_name,
            score=event.score,
            passed=event.passed,
            failure_types=event.failure_types,
            severity=event.severity,
            findings=event.findings,
            analyzed_at=event.analyzed_at,
        )
        session.add(row)
        session.commit()
        logger.info('stored {"event_key": "%s", "run_id": "%s"}', key, event.run_id)
        return {
            "stored": True,
            "idempotent_replay": False,
            "event_key": key,
            "scorecard_id": row.id,
        }
    except IntegrityError as exc:
        session.rollback()
        logger.warning(
            "concurrent scorecard insert for %s (%s); treating as replay",
            f"{event.run_id}:{event.analyzed_at}",
            str(exc).split("\n")[0][:160],
        )
        return {
            "stored": False,
            "idempotent_replay": True,
            "event_key": event_key_for(event.run_id, event.analyzed_at),
        }
    except Exception as exc:
        session.rollback()
        error = f"{type(exc).__name__}: {exc}"[:300]
        logger.exception("scorecard persistence FAILED: %s", error)
        return {"stored": False, "error": error}
    finally:
        session.close()
