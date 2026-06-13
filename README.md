# Cloptima LLM Observability Python SDK

Capture LLM usage telemetry from your application and send it to Cloptima for cost reporting, attribution, and analytics.

Use this SDK when you want visibility into LLM usage without replacing your existing provider clients, retry policies, authentication, or application-level security controls.

## Install

```bash
pip install cloptima-llm-observability
```

If you want to use the `httpx` transport helpers, install the optional extra:

```bash
pip install "cloptima-llm-observability[httpx]"
```

## Configuration

Common environment variables:

| Variable | Required | Purpose |
| --- | --- | --- |
| `CLOPTIMA_LLM_OBSERVABILITY_API_KEY` | Yes | Cloptima API key for telemetry writes |
| `CLOPTIMA_LLM_OBSERVABILITY_APP_ID` | Yes | Application or service identifier |
| `CLOPTIMA_LLM_OBSERVABILITY_ENABLED` | No | Explicitly enable or disable the SDK |

Recommended optional environment variables:

| Variable | Purpose |
| --- | --- |
| `CLOPTIMA_LLM_OBSERVABILITY_ENVIRONMENT` | Deployment environment such as `dev`, `staging`, or `prod`. Defaults to `production`, so set this explicitly when testing outside production. |
| `CLOPTIMA_LLM_OBSERVABILITY_TEAM_ID` | Team or ownership group |

The SDK sends bearer-authenticated HTTPS requests to `https://api.cloptima.ai/v1/ai/integrations/sdk/events` by default.

## Quick start

Use `observe_call(...)` at the point where your application already invokes an LLM provider or an internal AI helper.

```python
from cloptima_llm_observability import (
    extract_openai_usage,
    init_from_env,
)

cloptima = init_from_env()

result = cloptima.observe_call(
    provider="openai",
    model="gpt-4.1-mini",
    call=lambda: summary_service.generate(prompt),
    extract_usage=extract_openai_usage,
    feature_id="summaries",
    workflow_id="support-agent",
    team_id="customer-support",
    fire_and_forget=False,
)
```

This integration style works well because it:

- keeps your existing provider integration intact
- captures the most accurate model and feature context
- avoids SDK-specific coupling throughout your codebase
- works well with existing wrappers and shared AI services

## Async and streaming calls

If your application already uses async calls or streaming responses, use the matching helpers:

```python
result = await cloptima.observe_async_call(
    provider="anthropic",
    model="claude-3-5-sonnet",
    call=lambda: assistant_client.reply(messages),
    feature_id="chat_reply",
)

async for chunk in cloptima.observe_async_stream_call(
    provider="openai",
    model="gpt-4.1-mini",
    call=lambda: stream_client.stream(prompt),
    feature_id="live_answer",
):
    print(chunk)
```

## Shared transport integration

If your application centralizes outbound LLM calls behind a shared `httpx` transport, instrument that boundary instead:

```python
import httpx

from cloptima_llm_observability import init_from_env, instrument_httpx_transport

cloptima = init_from_env()
transport = instrument_httpx_transport(
    httpx.HTTPTransport(),
    cloptima=cloptima,
    provider="openai",
    model="gpt-4o-mini",
    fire_and_forget=False,
)
client = httpx.Client(transport=transport)
```

This is useful for broad coverage, but it has less application context than `observe_call(...)`. Prefer `observe_call(...)` when you already know the provider, model, and feature at the call site.

## OTLP mode

The SDK supports two delivery modes:

- `cloptima_http`
- `otlp_http`

Use `otlp_http` when you want the SDK to send OpenTelemetry-compatible payloads to Cloptima's OTLP-compatible receiver instead of the standard SDK telemetry endpoint.

`otlp_http` is still a Cloptima delivery mode. The SDK keeps the OTLP route fixed and only lets you override the Cloptima API domain or environment.

Advanced configuration:

- `CLOPTIMA_LLM_OBSERVABILITY_DELIVERY_MODE` selects `cloptima_http` or `otlp_http`
- `CLOPTIMA_LLM_OBSERVABILITY_API_BASE_URL` overrides the Cloptima API domain while the SDK keeps the ingest routes fixed
- `CLOPTIMA_LLM_OBSERVABILITY_OTLP_SERVICE_NAME` and `CLOPTIMA_LLM_OBSERVABILITY_OTLP_SERVICE_VERSION` customize OTLP service metadata

## Attribution fields

The most useful fields for reporting and ownership are:

- `app_id`
- `environment`
- `team_id`
- `feature_id`
- `workflow_id`
- `cost_center`
- `business_unit`
- `tenant_id`
- `customer_segment`
- `cloud_account_id`
- `cluster_id`
- `repository_id`

You can pass them through `default_attribution`, or directly on `observe_call(...)` / `observe_stream_call(...)`.

## Metadata controls

Use `metadata_policy` to control what custom metadata is retained:

- `metadata_only`
- `allowlisted_metadata`
- `strict_finops`
- `debug_observability`

Sensitive-looking keys such as prompts, messages, credentials, and secrets are treated conservatively by default.

## Validation helpers

These helpers are useful when you want to inspect payloads locally before sending traffic to Cloptima:

- `preview_event_payload(...)`
- `preview_batch_payload(...)`
- `preview_otlp_request(...)`
- `validate_payload(...)`

They return payload previews in memory and do not send network traffic.

## Examples

See the `examples/` directory for:

- OpenAI call-site instrumentation
- OpenTelemetry-compatible delivery to Cloptima
- Anthropic call-site instrumentation
- Gemini call-site instrumentation
- custom wrapper integration
- httpx transport integration

## Public API

Stable core surface:

- `CloptimaLLMObservability`
- `init_from_env`
- `disabled_client`
- `observe`
- `observe_call`
- `observe_async_call`
- `observe_stream`
- `observe_stream_call`
- `record`
- `record_batch`
- `record_async`
- provider usage extractors

Additional helper surface:

- `instrument_httpx_client`
- `instrument_httpx_transport`
- `instrument_openai_compatible_response`
- `instrument_openai_compatible_stream`
- `ainstrument_openai_compatible_response`
- `ainstrument_openai_compatible_stream`
- `instrument_fastapi_request_context`
- `instrument_flask_request_context`

## Troubleshooting

No telemetry arrives:

- verify the API key is valid for Cloptima telemetry ingestion
- check `client.is_enabled()`
- if you use advanced routing overrides, verify `CLOPTIMA_LLM_OBSERVABILITY_API_BASE_URL` points at the intended Cloptima environment
- inspect a sample event with `validate_payload(preview_event_payload(...))`

Configuration behavior:

- `init_from_env()` returns a disabled pass-through client when configuration is absent
- if you explicitly enable the SDK with incomplete config, initialization stays non-blocking by default unless `strict=True`

## Payload contracts

- single event schema: `cloptima.llm.event.v1`
- batch schema: `cloptima.llm.batch.v1`

SDK envelopes also include `sdk_delivery_stats` for delivery monitoring.

## Support

- Issues: `https://github.com/cloptima/cloptima-llm-observability-python/issues`
- Security: see `SECURITY.md`
- Product support: `hello@cloptima.ai`
