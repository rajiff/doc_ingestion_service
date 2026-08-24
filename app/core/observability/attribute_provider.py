from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Protocol

@dataclass(frozen=True)
class AttributeContext:
    """
    Context passed to a dynamic telemetry attribute provider.

    `arguments` contains normalized function arguments mapped by
    parameter name.

    Example:

        {
            "self": <DocumentService>,
            "file_stream": <BinaryIO>,
            "client_doc_id": "DOC-123",
            "force_reingest": False,
        }
    """

    arguments: Mapping[str, Any]

    def get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """
        Safely get a function argument by its parameter name.
        """
        return self.arguments.get(
            name,
            default,
        )


class AttributeProvider(Protocol):
    """
    Contract for providing dynamic telemetry attributes.

    Implementations receive the normalized invocation context and
    return telemetry attributes to be attached to the current span.
    """

    def __call__(
        self,
        context: AttributeContext,
    ) -> Mapping[str, Any] | None:
        ...
