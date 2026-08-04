import logging
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from app.core.config import settings

logger = logging.getLogger(__name__)

def setup_telemetry(app: FastAPI):
    """
    Instruments FastAPI with OpenTelemetry for tracing request latency & bottlenecks.
    """
    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        logger.info("OTEL Exporter not set %s", settings.OTEL_EXPORTER_OTLP_ENDPOINT)
        return

    logger.info("OTEL Exporter for project %s set to %s", settings.PROJECT_NAME, settings.OTEL_EXPORTER_OTLP_ENDPOINT)

    # 1. Define Resource attributes (Sets the service name in Jaeger/Tempo)
    resource = Resource.create(attributes={
        SERVICE_NAME: settings.PROJECT_NAME
    })

    # 2. Pass resource into TracerProvider
    provider = TracerProvider(resource=resource)

    # 3. Configure Exporter
    processor = BatchSpanProcessor(
        OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, 
            insecure=True
        )
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # 4. Auto-instrument FastAPI routes
    FastAPIInstrumentor.instrument_app(app)
