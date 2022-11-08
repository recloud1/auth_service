from flask import Flask
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_tracer(
        app: Flask,
        jaeger_host: str,
        jaeger_port: int,
        service_name: str = 'Auth Service'
) -> None:
    jaeger_exporter = JaegerExporter(agent_host_name=jaeger_host, agent_port=jaeger_port)
    span_processor = BatchSpanProcessor(jaeger_exporter)

    resource = Resource.create({SERVICE_NAME: service_name})
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(span_processor)

    trace.set_tracer_provider(tracer_provider)

    FlaskInstrumentor().instrument_app(app)
