from typing import Any, Callable, ParamSpec, TypeVar

from app.core.observability.semantic_schema import O11yAppAttributes, O11yDecoratorType
from app.core.observability.decorators import instrument

P = ParamSpec("P")
R = TypeVar("R")

def business_operation(
    func: Callable[P, R] | None = None,
    *,
    label: str | None = None,
    capability: str | None = None,
    attributes: dict[str, Any] | None = None,
):
    """
    Decorator for instrumenting a business-level operation.

    Avoid adding any PII and sensitive data as attribute or any other field

    A business operation represents a meaningful application or
    domain capability, for example:

    Use type BusinessCapability for defining the capability of the operation:
    - knowledge.answer_question
    - document.ingest
    - tutorial.generate
    - quiz.generate
    - presentation.generate

    The decorator creates an OpenTelemetry span through the generic
    @observe decorator and adds business-level semantic attributes.

    Supports:

        @business_operation
        def your_business_operation():

        @business_operation()
        async def your_business_operation():

        @business_operation(
            name="knowledge.answer_question",
            capability="knowledge_assistance",
        )
        async def your_business_operation():
    """

    def decorator(
        target: Callable[P, R],
    ) -> Callable[P, R]:
        operation_name = label or target.__qualname__

        business_attributes = {
            O11yAppAttributes.OBSERVABILITY_DECORATOR: O11yDecoratorType.BUSINESS,
            O11yAppAttributes.BUSINESS_OPERATION_NAME: operation_name,
        }

        if capability is not None:
            business_attributes[
                O11yAppAttributes.BUSINESS_CAPABILITY
            ] = capability

        if attributes:
            business_attributes.update(
                attributes
            )

        return instrument(
            name=operation_name,
            attributes=business_attributes
        )(target)

    if func is not None:
        return decorator(func)

    return decorator
