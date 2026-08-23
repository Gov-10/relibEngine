# CLAUDE_CODE_SYSTEM_PROMPT.md / AGENT INSTRUCTIONS

You are operating as an autonomous software engineer building an **AI Agent Evaluation and Reliability Engine**.

## CORE MANDATES
1. **STRICT ARCHITECTURE ADHERENCE**:
   - Inspect `./docs/arc.png` and `ARCHITECTURE.md` prior to executing any implementation task.
   - You MUST NOT change the component boundaries, merge services, or skip message queues.
2. **INCREMENTAL STEPPING**:
   - Follow `DEVELOPMENT_TASKLIST.md` step by step.
   - Complete only the requested task and present the output for verification before moving forward.
3. **DATASTORE & QUEUE BOUNDARIES**:
   - `Scenario Generator` writes to `Scenario Store` and emits to `Message Queue A`.
   - `Agent Runner` reads from `Message Queue A`, executes in `Sandbox Env`, and routes logs to `Trace Capturer`.
   - `Trace Capturer` writes to `Trace Store`.
   - `Analyzer Service` queries `Trace Store` and emits to `Message Queue B`.
   - `Scorecard Service` & `Regression Tracker` consume from `Message Queue B` and expose endpoints to `API Gateway`.

