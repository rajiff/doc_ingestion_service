from typing import Any, Callable, ParamSpec, TypeVar

from app.core.observability.semantic_schema import O11yDecoratorType, O11yAppAttributes
from app.core.observability.decorators.instrument import instrument

# generic placeholders for static type checkers
# captures the exact arguments and keyword arguments of a callable and
# allows you to forward them to another callable without losing type information.
P = ParamSpec("P") # InputParams
R = TypeVar("R") # ReturnType

def observe(
    func: Callable[P, R] | None = None,
    *,
    label: str | None = None,
    attributes: dict[str, Any] | None = None,
):
    """
    Observe the execution of a synchronous or asynchronous function.

    Creates an OpenTelemetry span and automatically:

    - Establishes parent-child trace relationships
    - Records function execution duration
    - Records exceptions
    - Marks failed spans with ERROR status
    - Adds common observability attributes
    - Supports sync and async functions

    Arguments:
    - func (Callable): The function to be observed
    - label (str): Optional label of span, group spans in the trace viewer
    - attributes (dict): Optional additional attributes to be added to the span

    Usage:

        @observe
        def your_operation():
            ...

        @observe()
        async def some_operation():
            ...

        @observe(name="rag.retrieve")
        async def rag_retrieve_operation():

        @observe
        async def my_function():
            ...
    """

    def decorator(
        target: Callable[P, R],
    ) -> Callable[P, R]:

        span_name = label or target.__qualname__

        span_attributes = {
            O11yAppAttributes.OBSERVABILITY_DECORATOR: O11yDecoratorType.OBSERVE,
            **(attributes or {}), # merge with user attributes
        }

        return instrument(
            name=span_name,
            attributes=span_attributes,
        )(target)

    # Supports:
    #
    # @observe
    #
    # without parentheses, no arguments, and no keyword arguments.
    if func is not None:
        return decorator(func)

    # Supports:
    #
    # @observe()
    # @observe(name="...")
    #
    return decorator
