from pydantic import BaseModel, ConfigDict, Field


class ToolDefinition(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    input_schema: dict = Field(default_factory=dict)
    mock_config: dict | None = None


class ScenarioGenerationRequest(BaseModel):
    agent_name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    task_domain: str = Field(default="general", max_length=100)
    system_prompt: str = Field(min_length=1)
    prompt_version: str | None = Field(default=None, max_length=20)
    tools: list[ToolDefinition] = Field(default_factory=list)
    num_scenarios: int = Field(default=3, ge=1, le=10)


class EvaluationCriterionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    criterion_type: str
    weight: float
    config: dict


class GeneratedScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    severity: str
    payload: dict
    expected_behavior: str | None = None
    criteria: list[EvaluationCriterionOut] = []


class ScenarioJobOut(BaseModel):
    scenario_id: int
    job_id: str
    published: bool
    detail: str | None = None


class ScenarioGenerationResponse(BaseModel):
    agent_id: int
    prompt_id: int
    generated_by: str
    scenarios: list[GeneratedScenarioOut]
    jobs: list[ScenarioJobOut] = []
