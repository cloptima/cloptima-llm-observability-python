import json
import urllib.request

from cloptima_llm_observability import extract_openai_usage, init_from_env

INGEST_URL = "https://sdk-ingest.example.cloptima.ai/sdk/events"


class _FakeResponse:
    status = 202

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return b"{}"


class SummaryService:
    def generate_summary(self):
        return {
            "id": "chatcmpl-wrapper-example",
            "model": "gpt-4.1-mini",
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 7,
                "total_tokens": 19,
            },
        }


def main() -> None:
    original_urlopen = urllib.request.urlopen

    def fake_urlopen(request, timeout):
        payload = json.loads((request.data or b"{}").decode("utf-8"))
        if payload.get("metadata", {}).get("integration_mode") != "shared_service":
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
        summary_service = SummaryService()
        client.observe_call(
            provider="openai",
            model="gpt-4.1-mini",
            call=lambda: summary_service.generate_summary(),
            extract_usage=extract_openai_usage,
            fire_and_forget=False,
            feature_id="support_summary",
            metadata={"integration_mode": "shared_service"},
        )
    finally:
        urllib.request.urlopen = original_urlopen


if __name__ == "__main__":
    main()
