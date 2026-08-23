# SYSTEM ARCHITECTURE & IMPLEMENTATION DIRECTIVES

## Project Overview
This project is an **AI Agent Evaluation and Reliability Engine**—a CI/CD pipeline for autonomous AI agents.
It automatically generates adversarial scenarios, executes agents in sandboxed environments, captures traces, classifies failure modes, and tracks reliability regressions across versions.

## ARCHITECTURAL DIAGRAM REFERENCE
> **IMPORTANT FOR VISION-CAPABLE AGENTS**:
> An architectural diagram image is stored at `./docs/arc.png`.
> If your tool/agent supports multimodal image reading (e.g., Claude 3.5/3.7 Sonnet, Gemini 1.5/2.5 Pro, GPT-4o), inspect `./docs/arc.png` to cross-verify structural topologies, directional arrow flows, message queues, and component relationships.

## NON-NEGOTIABLE ARCHITECTURAL BOUNDARIES
DO NOT modify, simplify, or refactor the overall system architecture. All code generated MUST strictly adhere to the defined services, databases, and message queues listed below and depicted in `./docs/arc.png`.

```
                  ┌──────────┐
                  │ Auth db  │
                  └────▲─────┘
                       │
                  ┌────┴─────┐
                  │ Auth Svc │
                  └────▲─────┘
                       │
┌──────────┐      ┌────▼─────┐      ┌──────────┐             ┌──────────────┐
│ Frontend ├─────►│   API    ├─────►│ Scenario ├────────────►│ Scenario Store│
└──────────┘      │ Gateway  │      │ Generator│             └──────────────┘
                  └▲───▲────▲┘      └────┬─────┘
                   │   │    │            │
                   │   │    │      [Message Queue A]
                   │   │    │            │
                   │   │    │            ▼
                   │   │    │       ┌─────────────────────────┐      ┌─────────────┐
                   │   │    │       │ Agent Runner & Planner  ├─────►│ Sandbox env │
                   │   │    │       │ (Temporal Orchestrator) │      └─────────────┘
                   │   │    │       └────────────┬────────────┘
                   │   │    │                    │
                   │   │    │                    ▼
                   │   │    │               ┌──────────┐
                   │   │    │               │  Trace   │
                   │   │    │               │ Capturer │
                   │   │    │               └────┬─────┘
                   │   │    │                    │
                   │   │    │                    ▼
                   │   │    │               ┌──────────┐
                   │   │    │               │  Trace   │
                   │   │    │               │  store   │
                   │   │    │               └────┬─────┘
                   │   │    │                    │ (Query)
                   │   │    │                    ▼
                   │   │    │               ┌──────────┐
                   │   │   ┌┴──────────┐    │ Analyzer │
                   │   │   │ Scorecard │◄───┤ & Rel.   │
                   │   │   └───────────┘    │ Service  │
                   │   │                    └────┬─────┘
                   │   │                         │
                   │   │                   [Message Queue B]
                   │   │                         │
                   │   └─────────────────────────┼──────┐
                   │                             │      │
                   └─────────────────────────────┴──────┼──────┐
                                                        │      │
                                                        ▼      ▼
                                               ┌──────────┐  ┌──────────┐
                                               │Scorecard │  │Regression│
                                               │ Service  │  │ Tracker  │
                                               └──────────┘  └──────────┘
```

### Microservices & Components Map
1. **Frontend**: Web UI for configuring test suites, visualizing trace replays, displaying scorecards, and monitoring regression trends. Connects strictly via `API Gateway`.
2. **API Gateway**: Reverse proxy / gateway layer. Routes requests to `Auth Service`, `Scenario Generator`, `Scorecard Service`, and `Regression Tracker`.
3. **Auth Service & Auth DB**: Handles user authentication, API key validation, and RBAC. Connects to `Auth DB`.
4. **Scenario Generator**: Ingests agent tool definitions, system prompts, and task domains. Automatically crafts adversarial scenarios.
   - **Outputs to**: Writes scenario records to `Scenario Store` and pushes job payloads to `Message Queue A`.
5. **Scenario Store**: Dedicated persistent datastore (PostgreSQL / MongoDB) holding all generated test cases and attack parameters.
6. **Message Queue A (Scenario Job Queue)**: Asynchronous queue (RabbitMQ / Redis / NATS) decoupling scenario generation from agent execution.
7. **Agent Runner and Planner (Temporal Orchestrator)**: Uses Temporal workflow engine to coordinate target agent steps, handle timeouts, retries, and manage state.
8. **Sandbox Env**: Isolated execution sandbox (Docker/gVisor/E2B) running mocked target APIs, tools, and the agent under test.
9. **Trace Capturer**: Intercepts step-by-step LLM calls, tool interactions, state transitions, and console output from `Agent Runner`.
10. **Trace Store**: Red-flagged high-throughput datastore (TimescaleDB / ClickHouse / Elasticsearch) storing execution traces.
11. **Analyzer and Reliability Service**: Pulls execution logs via SQL/Query interface from `Trace Store`. Evaluates failure modes (tool loops, hallucinated confidence, goal drift, safety guardrail violations).
12. **Message Queue B (Analysis Event Queue)**: Asynchronous event bus carrying evaluated scoring payloads to downstream reporting services.
13. **Scorecard Service**: Consumes from `Message Queue B` to calculate point-in-time reliability scorecards. Serves queries via `API Gateway`.
14. **Regression Tracker**: Consumes from `Message Queue B` to maintain historical performance metrics across agent versions and code commits. Serves queries via `API Gateway`.

---

## STRICT CODING INSTRUCTIONS
1. **REFER TO DIAGRAM**: Check `./docs/arc.png` or the ASCII diagram above before creating new files or routes.
2. **NO COMPONENT CONSOLIDATION**: Do NOT merge microservices into single monolithic scripts. Each box in the diagram must map to an isolated module or service folder.
3. **DATA FLOW COMPLIANCE**:
   - `Trace Capturer` ONLY writes to `Trace Store`.
   - `Analyzer Service` ONLY queries `Trace Store` (does not directly stream from `Trace Capturer`).
   - `Scenario Generator` pushes to `Message Queue A`; `Agent Runner` consumes from `Message Queue A`.
   - `Analyzer Service` pushes to `Message Queue B`; `Scorecard` and `Regression Tracker` consume from `Message Queue B`.

