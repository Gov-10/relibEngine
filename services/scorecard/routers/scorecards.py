from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Scorecard
from schemas import ScorecardOut


router = APIRouter(tags=["scorecards"])


@router.get("/scorecards", response_model=list[ScorecardOut])
def list_scorecards(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return (
        db.query(Scorecard)
        .order_by(Scorecard.captured_at.desc(), Scorecard.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/scorecards/run/{run_id}", response_model=list[ScorecardOut])
def get_scorecards_for_run(run_id: str, db: Session = Depends(get_db)):
    return (
        db.query(Scorecard)
        .filter(Scorecard.run_id == run_id)
        .order_by(Scorecard.captured_at.desc(), Scorecard.id.desc())
        .all()
    )


@router.get("/scorecards/run/{run_id}/latest", response_model=ScorecardOut)
def get_latest_scorecard(run_id: str, db: Session = Depends(get_db)):
    latest = (
        db.query(Scorecard)
        .filter(Scorecard.run_id == run_id)
        .order_by(Scorecard.captured_at.desc(), Scorecard.id.desc())
        .first()
    )
    if latest is None:
        raise HTTPException(status_code=404, detail=f"no scorecard for run: {run_id}")
    return latest
