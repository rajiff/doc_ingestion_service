from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from app.core.config import settings

def setup_telemetry(app: FastAPI):
    """
    Instruments FastAPI with OpenTelemetry for tracing request latency & bottlenecks.
    """
    if not settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        return

    provider = TracerProvider()
    processor = BatchSpanProcessor(
        OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT, insecure=True)
    )
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    # Auto-instrument FastAPI routes
    FastAPIInstrumentor.instrument_app(app)
