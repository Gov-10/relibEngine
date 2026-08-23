from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import RegressionResult
from schemas import RegressionResultOut


router = APIRouter(tags=["regressions"])


@router.get("/regressions", response_model=list[RegressionResultOut])
def list_regressions(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(RegressionResult)
        .order_by(RegressionResult.captured_at.desc(), RegressionResult.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/regressions/agent/{agent_name}", response_model=list[RegressionResultOut])
def get_agent_history(agent_name: str, db: Session = Depends(get_db)):
    return (
        db.query(RegressionResult)
        .filter(RegressionResult.agent_name == agent_name)
        .order_by(RegressionResult.captured_at.desc(), RegressionResult.id.desc())
        .all()
    )


@router.get("/regressions/agent/{agent_name}/latest", response_model=RegressionResultOut)
def get_latest_for_agent(agent_name: str, db: Session = Depends(get_db)):
    latest = (
        db.query(RegressionResult)
        .filter(RegressionResult.agent_name == agent_name)
        .order_by(RegressionResult.captured_at.desc(), RegressionResult.id.desc())
        .first()
    )
    if latest is None:
        raise HTTPException(
            status_code=404, detail=f"no regression results for agent: {agent_name}"
        )
    return latest


@router.get("/regressions/run/{run_id}", response_model=RegressionResultOut)
def get_result_for_run(run_id: str, db: Session = Depends(get_db)):
    result = (
        db.query(RegressionResult)
        .filter(RegressionResult.run_id == run_id)
        .order_by(RegressionResult.captured_at.desc(), RegressionResult.id.desc())
        .first()
    )
    if result is None:
        raise HTTPException(
            status_code=404, detail=f"no regression result for run: {run_id}"
        )
    return result
