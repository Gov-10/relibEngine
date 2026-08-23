import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from classifier import classify, explain
from database import get_db
from messaging import get_topic, publish_analysis_event
from models import Run, TraceStep
from schemas import AnalysisRequest, ReliabilityResult


logger = logging.getLogger("analyzer.analysis")

router = APIRouter(tags=["analysis"])


def _analyze(db: Session, run_id: str, request: AnalysisRequest) -> ReliabilityResult:
    run = db.query(Run).filter(Run.run_id == run_id).one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail=f"run not found: {run_id}")
    steps = (
        db.query(TraceStep)
        .filter(TraceStep.run_id == run.id)
        .order_by(TraceStep.step_index)
        .all()
    )

    analysis = classify(run, steps)
    analyzed_at = datetime.now(timezone.utc).isoformat()

    result = ReliabilityResult(
        run_id=run.run_id,
        trace_id=run.trace_id,
        scenario_ref=run.scenario_ref,
        agent_name=run.agent_name,
        score=analysis["score"],
        passed=analysis["passed"],
        failure_types=analysis["failure_types"],
        severity=analysis["severity"],
        findings=analysis["findings"],
        stats=analysis["stats"],
        explanation="",
        analyzed_at=analyzed_at,
    )
    if request is None or request.include_explanation:
        result.explanation = explain(result.model_dump())
    return result


def _emit_event(result: ReliabilityResult) -> None:
    try:
        location = publish_analysis_event(result.model_dump(mode="json"))
        result.event_published = True
        result.event_topic = get_topic()
        logger.info(
            "analysis event delivered for %s at %s", result.run_id, location
        )
    except Exception as exc:
        result.event_published = False
        result.event_error = f"{type(exc).__name__}: {exc}"[:300]
        logger.warning(
            "analysis event NOT published for %s (%s)",
            result.run_id,
            result.event_error,
        )


@router.post("/analysis/runs/{run_id}", response_model=ReliabilityResult)
def analyze_run(
    run_id: str,
    request: AnalysisRequest | None = None,
    db: Session = Depends(get_db),
):
    result = _analyze(db, run_id, request or AnalysisRequest())
    _emit_event(result)
    return result


@router.get("/analysis/runs/{run_id}", response_model=ReliabilityResult)
def get_analysis(
    run_id: str,
    include_explanation: bool = True,
    db: Session = Depends(get_db),
):
    return _analyze(db, run_id, AnalysisRequest(include_explanation=include_explanation))
