from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from opentelemetry.trace import SpanKind

class O11yDecoratorType(str, Enum):
    OBSERVE = "observe"
    BUSINESS = "business"
    BUSINESS_STEP = "business_step"
    AI = "ai"

class BusinessCapability(str, Enum):
    KNOWLEDGE_ASSISTANCE = "knowledge_assistance"
    DOCUMENT_INGESTION = "document_ingestion"
    DOCUMENT_QUERY = "document_query"
    CONTENT_GENERATION = "content_generation"
    ASSESSMENT_GENERATION =  "assessment_generation"

class BusinessStepType(str, Enum):
    VALIDATION = "validation"
    RETRIEVAL = "retrieval"
    TRANSFORMATION = "transformation"
    ENRICHMENT = "enrichment"
    PERSISTENCE = "persistence"
    ORCHESTRATION = "orchestration"
    WORKFLOW = "workflow"

class AiOperationType(str, Enum):
    AGENT = "agent"
    CHAIN = "chain"
    RETRIEVAL = "retrieval"
    RERANK = "rerank"
    EMBEDDING = "embedding"
    GENERATION = "generation"
    TOOL = "tool"
    EVALUATION = "evaluation"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"

class O11yAppAttributes(str, Enum):
    OBSERVABILITY_DECORATOR = "app.observability.decorator"
    OPERATION_TYPE = "app.operation.type"
    BUSINESS_CAPABILITY = "app.business.capability"
    BUSINESS_OPERATION_NAME = "app.business.operation.name"
    BUSINESS_STEP_NAME = "app.business.step.name"
    BUSINESS_STEP_TYPE = "app.business.step.type"

@dataclass(frozen=True)
class O11yObservationMetadata:
    name: str
    decorator_type: O11yDecoratorType
    span_kind: SpanKind = SpanKind.INTERNAL
    attributes: dict[str, Any] = field(
        default_factory=dict,
    )
    business_capability: str | None = None
    business_step_type: str | None = None
    ai_operation_type: AiOperationType | None = None
    agent_name: str | None = None
    capture_args: bool = False
    capture_result: bool = False
