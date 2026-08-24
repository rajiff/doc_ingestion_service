import inspect
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar

from opentelemetry.trace import SpanKind, Status, StatusCode

from app.core.observability.telemetry import get_tracer

# generic placeholders for static type checkers
# captures the exact arguments and keyword arguments of a callable and
# allows you to forward them to another callable without losing type information.
P = ParamSpec("P") # InputParams
R = TypeVar("R") # ReturnType

def instrument(
    *,
    name: str | None = None,
    attributes: dict[str, Any] | None = None,
    span_kind: SpanKind = SpanKind.INTERNAL
):
    """
    Internal instrumentation primitive for execution of a synchronous or
    asynchronous function.

    Creates an General OpenTelemetry span and automatically:
    """

    def decorator(
        target: Callable[P, R],
    ) -> Callable[P, R]:

        if inspect.iscoroutinefunction(target):

            @wraps(target)
            async def async_wrapper(
                *args: P.args,
                **kwargs: P.kwargs,
            ) -> R:

                tracer = get_tracer(target.__module__)

                with tracer.start_as_current_span(
                    name=name,
                    kind=span_kind
                ) as span:

                    # Safely add attributes to the current span
                    _apply_attributes(
                        span,
                        attributes,
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
                name=name,
                kind=span_kind
            ) as span:

                # Safely add attributes to the current span
                _apply_attributes(
                    span,
                    attributes,
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
