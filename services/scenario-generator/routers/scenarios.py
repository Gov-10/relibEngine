import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from generator import ScenarioGenerationError, generate_drafts
from messaging import publish_scenario_job
from models import Agent, AgentPrompt, EvaluationCriterion, Scenario, Tool
from schemas import (
    GeneratedScenarioOut,
    ScenarioGenerationRequest,
    ScenarioGenerationResponse,
    ScenarioJobOut,
)


logger = logging.getLogger(__name__)

router = APIRouter(tags=["scenarios"])


def _upsert_agent(db: Session, payload: ScenarioGenerationRequest) -> Agent:
    agent = db.query(Agent).filter(Agent.name == payload.agent_name).one_or_none()
    if agent is None:
        agent = Agent(
            name=payload.agent_name,
            description=payload.description,
            task_domain=payload.task_domain,
        )
        db.add(agent)
        db.flush()
    else:
        agent.description = payload.description or agent.description
        agent.task_domain = payload.task_domain
    existing = {t.name: t for t in agent.tools}
    incoming_names = {t.name for t in payload.tools}
    for td in payload.tools:
        if td.name in existing:
            row = existing[td.name]
            row.description = td.description
            row.input_schema = td.input_schema
            row.mock_config = td.mock_config
        else:
            db.add(
                Tool(
                    agent=agent,
                    name=td.name,
                    description=td.description,
                    input_schema=td.input_schema,
                    mock_config=td.mock_config,
                )
            )
    for name in set(existing) - incoming_names:
        db.delete(existing[name])
    return agent


@router.post("/scenarios/generate", response_model=ScenarioGenerationResponse)
def generate_scenarios(
    payload: ScenarioGenerationRequest, db: Session = Depends(get_db)
):
    try:
        generated_by, drafts = generate_drafts(payload)
    except ScenarioGenerationError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    try:
        agent = _upsert_agent(db, payload)
        version = payload.prompt_version or f"v{len(agent.prompts) + 1}"
        prompt_row = AgentPrompt(
            agent=agent, version=version, content=payload.system_prompt, is_active=True
        )
        db.add(prompt_row)
        db.flush()

        created: list[Scenario] = []
        for draft in drafts:
            criteria = draft.pop("criteria")
            scenario = Scenario(
                agent=agent,
                prompt=prompt_row,
                title=draft["title"],
                description=draft["description"],
                payload=draft["payload"],
                expected_behavior=draft["expected_behavior"],
                severity=draft["severity"],
            )
            db.add(scenario)
            db.flush()
            for crit in criteria:
                db.add(
                    EvaluationCriterion(
                        agent=agent,
                        scenario=scenario,
                        name=crit["name"],
                        criterion_type=crit["criterion_type"],
                        config=crit["config"],
                        weight=crit["weight"],
                    )
                )
            created.append(scenario)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Scenario Store persistence failure: {exc}"
        )

    return ScenarioGenerationResponse(
        agent_id=agent.id,
        prompt_id=prompt_row.id,
        generated_by=generated_by,
        scenarios=[GeneratedScenarioOut.model_validate(s) for s in created],
        jobs=_publish_jobs(agent, prompt_row, created),
    )


def _publish_jobs(agent: Agent, prompt_row: AgentPrompt, created: list[Scenario]) -> list[ScenarioJobOut]:
    jobs: list[ScenarioJobOut] = []
    for scenario in created:
        job = {
            "schema_version": 1,
            "job_id": str(uuid.uuid4()),
            "scenario_id": scenario.id,
            "agent_id": agent.id,
            "prompt_id": prompt_row.id,
            "agent_name": agent.name,
            "severity": scenario.severity,
            "produced_at": datetime.now(timezone.utc).isoformat(),
        }
        try:
            publish_scenario_job(job)
            jobs.append(
                ScenarioJobOut(scenario_id=scenario.id, job_id=job["job_id"], published=True)
            )
        except Exception as exc:
            logger.warning(
                "kafka publish failed for scenario %s (persisted, not enqueued): %s",
                scenario.id,
                exc,
            )
            jobs.append(
                ScenarioJobOut(
                    scenario_id=scenario.id,
                    job_id=job["job_id"],
                    published=False,
                    detail=str(exc)[:300],
                )
            )
    return jobs


@router.get("/scenarios/{scenario_id}", response_model=GeneratedScenarioOut)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    scenario = (
        db.query(Scenario).filter(Scenario.id == scenario_id).one_or_none()
    )
    if scenario is None:
        raise HTTPException(status_code=404, detail="scenario not found")
    return GeneratedScenarioOut.model_validate(scenario)
