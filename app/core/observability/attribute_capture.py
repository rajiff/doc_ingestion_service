from collections.abc import Mapping
from typing import Any

from app.core.observability.attribute_provider import (
    AttributeContext,
    AttributeProvider,
)

def capture_arguments(
    **argument_to_attribute: str,
) -> AttributeProvider:
    """
    Create an AttributeProvider that captures explicitly selected
    function arguments.

    Example:

        capture_arguments(
            client_doc_id="document.client.id",
            force_reingest="document.force_reingest",
        )

    This means:

        function argument:
            client_doc_id

        becomes telemetry attribute:
            document.client.id

    Only explicitly selected arguments are captured.
    """

    def provider(
        context: AttributeContext,
    ) -> Mapping[str, Any]:

        return {
            attribute_name: context.get(argument_name)
            for argument_name, attribute_name
            in argument_to_attribute.items()
        }

    return provider
