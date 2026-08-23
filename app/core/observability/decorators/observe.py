import inspect
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar

from opentelemetry.trace import SpanKind, Status, StatusCode

from app.core.observability.telemetry import get_tracer
from app.core.observability.semantic_schema import O11yDecoratorType

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
            "app.observability.decorator": O11yDecoratorType.OBSERVE,
            **(attributes or {}), # merge with user attributes
        }

        if inspect.iscoroutinefunction(target):

            @wraps(target)
            async def async_wrapper(
                *args: P.args,
                **kwargs: P.kwargs,
            ) -> R:

                tracer = get_tracer(target.__module__)

                with tracer.start_as_current_span(
                    name=span_name,
                    kind=SpanKind.INTERNAL,
                ) as span:

                    # Safely add attributes to the current span
                    _apply_attributes(
                        span,
                        span_attributes,
                    )

                    try:
                        return await target(
                            *args,
                            **kwargs,
                        )

                    except Exception as error:
                        _record_exception(
                            span,
                            error,
                        )
                        raise

            return async_wrapper

        @wraps(target)
        def sync_wrapper(
            *args: P.args,
            **kwargs: P.kwargs,
        ) -> R:
            tracer = get_tracer(target.__module__)

            with tracer.start_as_current_span(
                name=span_name,
                kind=SpanKind.INTERNAL,
            ) as span:

                # Safely add attributes to the current span
                _apply_attributes(
                    span,
                    span_attributes,
                )

                try:
                    return target(
                        *args,
                        **kwargs,
                    )

                except Exception as error:
                    _record_exception(
                        span,
                        error,
                    )
                    raise

        return sync_wrapper

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


def _apply_attributes(
    span,
    attributes: dict[str, Any],
) -> None:
    """
    Safely add attributes to the current span.

    None values are ignored because they are not valid
    OpenTelemetry attribute values.
    """

    for key, value in attributes.items():
        if value is not None:
            span.set_attribute(
                key,
                value,
            )

def _record_exception(
    span,
    error: Exception,
) -> None:
    """
    Record an exception using OpenTelemetry conventions.
    """
    span.record_exception(error)

    span.set_status(
        Status(
            status_code=StatusCode.ERROR,
            description=str(error),
        )
    )
