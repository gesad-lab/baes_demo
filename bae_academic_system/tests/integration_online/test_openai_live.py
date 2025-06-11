import re
import pytest

from llm.openai_client import OpenAIClient


@pytest.mark.integration_online
def test_openai_client_live_echo():
    """Simple live-call smoke test against GPT-4o-mini to verify connectivity."""
    client = OpenAIClient()
    prompt = "Return the single word BANANA in uppercase only."
    response = client.generate_response(prompt, temperature=0.0, max_tokens=5)
    # Response may contain whitespace or quotes, so use regex
    assert re.search(r"\bBANANA\b", response), f"Unexpected response: {response}" 