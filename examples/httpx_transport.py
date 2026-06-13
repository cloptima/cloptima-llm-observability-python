import json
import urllib.request
from types import SimpleNamespace

from cloptima_llm_observability import init_from_env, instrument_httpx_transport

INGEST_URL = "https://sdk-ingest.example.cloptima.ai/sdk/events"


class _FakeResponse:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return b"{}"


class FakeHttpxResponse:
    def __init__(self):
        self.status_code = 200
        self.headers = {"openai-request-id": "chatcmpl-httpx-example"}
        self.request = SimpleNamespace(
            headers={"x-request-id": "req-httpx-example"},
            method="POST",
            url=SimpleNamespace(
                host="api.openai.com",
                path="/v1/chat/completions",
                __str__=lambda self: "https://api.openai.com/v1/chat/completions",
            ),
        )

    def json(self):
        return {
            "id": "chatcmpl-httpx-example",
            "model": "gpt-4o-mini",
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 2,
                "total_tokens": 7,
            },
        }


class FakeTransport:
    def handle_request(self, request):
        return FakeHttpxResponse()


def main() -> None:
    original_urlopen = urllib.request.urlopen

    def fake_urlopen(request, timeout):
        payload = json.loads((request.data or b"{}").decode("utf-8"))
        if payload.get("metadata", {}).get("integration_mode") != "httpx_transport":
            raise RuntimeError("unexpected integration mode")
        return _FakeResponse()

    urllib.request.urlopen = fake_urlopen
    try:
        client = init_from_env(
            env={
                "CLOPTIMA_LLM_OBSERVABILITY_INGEST_URL": INGEST_URL,
                "CLOPTIMA_LLM_OBSERVABILITY_API_KEY": "cloptima_pat_example",
                "CLOPTIMA_LLM_OBSERVABILITY_APP_ID": "support-api",
                "CLOPTIMA_LLM_OBSERVABILITY_ENVIRONMENT": "dev",
            }
        )
        transport = instrument_httpx_transport(
            FakeTransport(),
            cloptima=client,
            provider="openai",
            model="gpt-4o-mini",
            metadata={"integration_mode": "httpx_transport"},
            fire_and_forget=False,
        )
        request = SimpleNamespace(
            headers={"x-request-id": "req-httpx-example"},
            method="POST",
            url=SimpleNamespace(
                host="api.openai.com",
                path="/v1/chat/completions",
                __str__=lambda self: "https://api.openai.com/v1/chat/completions",
            ),
        )
        transport.handle_request(request)
    finally:
        urllib.request.urlopen = original_urlopen


if __name__ == "__main__":
    main()
