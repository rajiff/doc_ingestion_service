import inspect

from collections.abc import Mapping
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar
from opentelemetry.trace import (
    SpanKind,
    Status,
    StatusCode
)
from app.core.observability.telemetry import get_tracer
from app.core.observability.attribute_capture import (
    AttributeContext,
    AttributeProvider,
)

# generic placeholders for static type checkers
# captures the exact arguments and keyword arguments of a callable and
# allows you to forward them to another callable without losing type information.
P = ParamSpec("P") # InputParams
R = TypeVar("R") # ReturnType

def instrument(
    *,
    name: str | None = None,
    attributes: Mapping[str, Any] | None = None,
    attribute_provider: AttributeProvider | None = None,
    span_kind: SpanKind = SpanKind.INTERNAL
):
    """
    Internal instrumentation primitive for execution of a synchronous or
    asynchronous function.

    Creates an General OpenTelemetry span and automatically:

    Supports:

    - synchronous functions
    - asynchronous functions
    - static telemetry attributes
    - dynamic telemetry attributes
    - normalized named arguments
    - default argument values
    - automatic parent-child trace relationships
    - exception recording
    - error span status

    Dynamic attribute providers receive an AttributeContext containing
    function arguments normalized by parameter name.
    """

    def decorator(
        target: Callable[P, R],
    ) -> Callable[P, R]:

        signature = inspect.signature(target)
        span_name = name or target.__qualname__

        def gather_dynamic_attributes(
            args: tuple[Any, ...],
            kwargs: Mapping[str, Any],
        ) -> Mapping[str, Any] | None:
            """
            Resolve function arguments to their parameter names.

            This makes instrumentation independent of whether callers
            used positional or keyword arguments.
            """

            if attribute_provider is None:
                return None

            try:
                bound_arguments = signature.bind(
                    *args,
                    **kwargs,
                )

                bound_arguments.apply_defaults()

                context = AttributeContext(
                    arguments=bound_arguments.arguments,
                )

                return attribute_provider(
                    context,
                )

            except Exception:
                # Observability must never cause the business
                # operation to fail.
                #
                # Instrumentation failures can be logged later.
                return None

        if inspect.iscoroutinefunction(target):

            @wraps(target)
            async def async_wrapper(
                *args: P.args,
                **kwargs: P.kwargs,
            ) -> R:

                tracer = get_tracer(target.__module__)

                with tracer.start_as_current_span(
                    name=span_name,
                    kind=span_kind
                ) as span:

                    # Safely add attributes to the current span
                    _apply_attributes(
                        span,
                        attributes,
                    )

                    dynamic_attributes = (
                        gather_dynamic_attributes(
                            args,
                            kwargs,
                        )
                    )

                    _apply_attributes(
                        span,
                        dynamic_attributes,
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

                dynamic_attributes = (
                    gather_dynamic_attributes(
                        args,
                        kwargs,
                    )
                )

                _apply_attributes(
                    span,
                    dynamic_attributes,
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

    if not attributes:
        return

    for key, value in attributes.items():
        try:
            if value is not None:
                span.set_attribute(
                    key,
                    value,
                )
        except Exception:
            # A telemetry attribute must never cause the
            # application request to fail.
            continue

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
