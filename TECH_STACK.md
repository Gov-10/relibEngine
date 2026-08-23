# TECH STACK & CODING CONSTRAINTS

## CORE FRAMEWORKS & TOOLS
- **Backend Framework**: Python (FastAPI) for all microservices.
- **Frontend Framework**: Next.js (React / TypeScript).
- **API Gateway**: Kong API Gateway (configured via declarative `kong.yml`).
- **LLM / AI Orchestration**: `langchain-groq` (Groq API integrations for scenario generation and failure analysis).
- **Database**: PostgreSQL.
- **Message Broker**: Apache Kafka (Kafka Topic A: `scenario-jobs`, Kafka Topic B: `analysis-events`).
- **Distributed Tracing**: Jaeger / OpenTelemetry protocol for trace capture and storage.

## MANDATORY CODING PATTERNS & SYNTAX RULES

### PostgreSQL & ORM Rules (CRITICAL)
- **Use Legacy SQLAlchemy 1.x Syntax**: Define models using classic `Column(...)` primitives.
- **Allowed Syntax**:
  ```python
  from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
  from sqlalchemy.ext.declarative import declarative_base

  Base = declarative_base()

  class User(Base):
      __tablename__ = "users"
      id = Column(Integer, primary_order=True, primary_key=True)
      username = Column(String(50), unique=True, nullable=False)
   ```
- **STRICTLY FORBIDDEN** : DO NOT use SQLAlchemy 2.0 Mapped[...] types, mapped_column(), or TypeAnnotation typing wrappers.
### FastAPI Rules
- Use Pydantic v2 for data validation schemas.
- Structure routes cleanly inside /routers for each respective service.

### Messaging and Tracing Rules
- Use kafka-python or  aiokafka for Kafka producers and consumers.
- Use opentelemetry-sdk / opentelemetry-exporter-jaeger for trace propagation in FastAPI middleware.
