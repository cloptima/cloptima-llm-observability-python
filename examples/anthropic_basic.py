import json
import urllib.request

from cloptima_llm_observability import extract_anthropic_usage, init_from_env

INGEST_URL = "https://sdk-ingest.example.cloptima.ai/sdk/events"


class _FakeResponse:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return b"{}"


def main() -> None:
    original_urlopen = urllib.request.urlopen

    def fake_urlopen(request, timeout):
        payload = json.loads((request.data or b"{}").decode("utf-8"))
        if payload.get("provider") != "anthropic" or payload.get("model") != "claude-3-5-sonnet":
            raise RuntimeError("unexpected telemetry payload")
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
        client.observe_call(
            provider="anthropic",
            model="claude-3-5-sonnet",
            call=lambda: {
                "id": "msg_anthropic_example",
                "model": "claude-3-5-sonnet",
                "usage": {
                    "input_tokens": 8,
                    "output_tokens": 4,
                },
            },
            extract_usage=extract_anthropic_usage,
            fire_and_forget=False,
            feature_id="agent_reply",
        )
    finally:
        urllib.request.urlopen = original_urlopen


if __name__ == "__main__":
    main()
