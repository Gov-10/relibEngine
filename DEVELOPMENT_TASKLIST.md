# DEVELOPMENT TASKLIST & EXECUTION PROTOCOL

## AI ASSISTANT EXECUTION INSTRUCTIONS
- **Work incrementally**: Implement ONE task at a time.
- **Reference Diagram**: Refer to `./docs/arc.png` (or `ARCHITECTURE.md`) before writing any service boilerplates.
- **Do not invent new services**: Maintain the exact 15 components outlined in the architecture spec.

## FLOW INSTRUCTIONS
- Agent Runner consumes Kafka and starts Temporal workflows.

---

### Phase 1: Environment Setup & Project Layout
- [ ] **Task 1.1**: Create project folder structure corresponding to architecture modules (`/services/auth`, `/services/scenario-generator`, `/services/agent-runner`, `/services/analyzer`, `/services/scorecard`, `/services/regression-tracker`, `/gateway`, `/frontend`, `/docs`).
- [ ] **Task 1.2**: Place system architecture diagram at `./docs/arc.png`.
- [ ] **Task 1.3**: Configure docker-compose setup containing message brokers (`Message Queue A`, `Message Queue B`) and data stores (`Auth DB`, `Scenario Store`, `Trace Store`).

### Phase 2: Datastores & Core Schemas
- [ ] **Task 2.1**: Implement `Auth DB` schema (Users, API Keys, Tenant IDs).
- [ ] **Task 2.2**: Implement `Scenario Store` schema (Agent Prompts, Tools Definition, Scenario Payloads, Evaluation Criteria).
- [ ] **Task 2.3**: Implement `Trace Store` schema (Trace IDs, Run IDs, Tool Call Log, System Prompts, Failure Flags, Latency Metrics).

### Phase 3: Scenario Generator & Execution Pipeline
- [ ] **Task 3.1**: Build `Scenario Generator` service to ingest agent tool specs and emit adversarial scenarios into `Scenario Store`.
- [ ] **Task 3.2**: Configure `Message Queue A` producer in `Scenario Generator` and worker consumer in `Agent Runner`.
- [ ] **Task 3.3**: Build `Agent Runner and Planner` utilizing Temporal workflow orchestrator.
- [ ] **Task 3.4**: Build `Sandbox Env` harness with mocked external tools and safe execution boundaries.
- [ ] **Task 3.5**: Build `Trace Capturer` middleware to stream execution logs directly into `Trace Store`.

### Phase 4: Analysis & Reliability Scoring Engine
- [ ] **Task 4.1**: Build `Analyzer and Reliability Service` to query `Trace Store` and evaluate failure taxonomies (tool-call loops, safety violations, hallucinated confidence).
- [ ] **Task 4.2**: Configure `Message Queue B` publisher in `Analyzer Service`.
- [ ] **Task 4.3**: Implement `Scorecard Service` worker consuming from `Message Queue B` to aggregate run quality metrics.
- [ ] **Task 4.4**: Implement `Regression Tracker` worker consuming from `Message Queue B` to compare metrics across agent versions.

### Phase 5: API Gateway & Frontend
- [ ] **Task 5.1**: Build `API Gateway` reverse proxy routing endpoints to Auth, Scenario Generator, Scorecard, and Regression Tracker.
- [ ] **Task 5.2**: Build `Frontend` dashboard (Next.js/React) to trigger scenario runs, view execution trace replays, and render regression charts.
