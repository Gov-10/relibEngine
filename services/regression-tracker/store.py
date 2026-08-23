import logging

from sqlalchemy.exc import IntegrityError

from database import ensure_database, get_engine, get_session_factory
from models import AnalysisEventLog, Base, RegressionResult
from regression import compute_regression


logger = logging.getLogger("regression-tracker.store")


def init() -> None:
    ensure_database()
    Base.metadata.create_all(get_engine(), checkfirst=True)


def event_key_for(run_id: str, analyzed_at: str) -> str:
    return f"{run_id}:{analyzed_at}"


def _latest_previous_result(session, event, exclude_key: str):
    return (
        session.query(RegressionResult)
        .filter(
            RegressionResult.agent_name == event.agent_name,
            RegressionResult.event_key != exclude_key,
        )
        .order_by(RegressionResult.analyzed_at.desc(), RegressionResult.id.desc())
        .first()
    )


def persist_analysis_event(event) -> dict:
    """Log the event and store its regression result. Idempotent per event key."""
    session = get_session_factory()()
    try:
        key = event_key_for(event.run_id, event.analyzed_at)
        existing = (
            session.query(AnalysisEventLog)
            .filter(AnalysisEventLog.event_key == key)
            .one_or_none()
        )
        if existing is not None:
            logger.info("duplicate analysis event %s; ignoring replay", key)
            return {
                "stored": False,
                "idempotent_replay": True,
                "event_key": key,
            }

        previous = _latest_previous_result(session, event, exclude_key=key)
        regression = compute_regression(event, previous)

        session.add(
            AnalysisEventLog(
                event_key=key,
                run_id=event.run_id,
                agent_name=event.agent_name,
                payload=event.model_dump(mode="json"),
            )
        )
        row = RegressionResult(
            event_key=key,
            run_id=event.run_id,
            trace_id=event.trace_id,
            scenario_ref=event.scenario_ref,
            agent_name=event.agent_name,
            agent_version=event.agent_version,
            git_commit=event.git_commit,
            score=event.score,
            passed=event.passed,
            failure_types=event.failure_types,
            severity=event.severity,
            previous_run_id=regression["previous_run_id"],
            previous_score=regression["previous_score"],
            score_delta=regression["score_delta"],
            failure_delta=regression["failure_delta"],
            regression_status=regression["regression_status"],
            analyzed_at=event.analyzed_at,
        )
        session.add(row)
        session.commit()
        logger.info(
            'stored {"event_key": "%s", "run_id": "%s", "status": "%s", '
            '"delta": %s}',
            key,
            event.run_id,
            regression["regression_status"],
            regression["score_delta"],
        )
        return {
            "stored": True,
            "idempotent_replay": False,
            "event_key": key,
            "regression_status": regression["regression_status"],
            "score_delta": regression["score_delta"],
        }
    except IntegrityError as exc:
        session.rollback()
        logger.warning(
            "concurrent insert for %s (%s); treating as replay",
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
        logger.exception("regression persistence FAILED: %s", error)
        return {"stored": False, "error": error}
    finally:
        session.close()
