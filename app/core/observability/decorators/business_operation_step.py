from typing import Any, Callable, ParamSpec, TypeVar

from app.core.observability.semantic_schema import O11yAppAttributes, O11yDecoratorType
from app.core.observability.decorators import observe

P = ParamSpec("P")
R = TypeVar("R")

def business_operation_step(
    func: Callable[P, R] | None = None,
    *,
    label: str | None = None,
    step_type: str | None = None,
    attributes: dict[str, Any] | None = None,
):
    """
    Decorator for instrumenting a meaingful step of business operation.

    Avoid adding any PII and sensitive data as attribute or any other field

    Use @business_operation_step for a meaningful workflow stage, not every function call.

    A business operation step represents a significant stage of a
    business workflow, for example:

    - validate_request
    - retrieve_context
    - rank_documents
    - generate_answer
    - persist_result

    This decorator delegates tracing mechanics to @observe and adds
    business-step semantic attributes.

    Supports:

        @business_operation_step
        def your_business_operation_step():

        @business_operation_step()
        async def your_business_operation_step():

        @business_operation_step(
            label="knowledge.retrieve_context",
            step_type="retrieval",
        )
        async def your_business_operation_step():
    """

    def decorator(
        target: Callable[P, R],
    ) -> Callable[P, R]:
        operation_name = label or target.__qualname__

        step_attributes = {
            O11yAppAttributes.OBSERVABILITY_DECORATOR: O11yDecoratorType.BUSINESS_STEP,
            O11yAppAttributes.BUSINESS_STEP_NAME: operation_name,
        }

        if step_type is not None:
            step_attributes[
                O11yAppAttributes.BUSINESS_STEP_TYPE
            ] = step_type

        if attributes:
            step_attributes.update(
                attributes
            )

        return observe(
            label=operation_name,
            attributes=step_attributes
        )(target)

    if func is not None:
        return decorator(func)

    return decorator
