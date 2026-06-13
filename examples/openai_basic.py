import json
import urllib.request

from cloptima_llm_observability import extract_openai_usage, init_from_env


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
        if payload.get("provider") != "openai" or payload.get("model") != "gpt-4.1-mini":
            raise RuntimeError("unexpected telemetry payload")
        return _FakeResponse()

    urllib.request.urlopen = fake_urlopen
    try:
        client = init_from_env(
            env={
                "CLOPTIMA_LLM_OBSERVABILITY_API_KEY": "cloptima_pat_example",
                "CLOPTIMA_LLM_OBSERVABILITY_APP_ID": "support-api",
                "CLOPTIMA_LLM_OBSERVABILITY_ENVIRONMENT": "dev",
            }
        )
        client.observe_call(
            provider="openai",
            model="gpt-4.1-mini",
            call=lambda: {
                "id": "chatcmpl-openai-example",
                "model": "gpt-4.1-mini",
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            },
            extract_usage=extract_openai_usage,
            fire_and_forget=False,
            feature_id="customer_summary",
        )
    finally:
        urllib.request.urlopen = original_urlopen


if __name__ == "__main__":
    main()
