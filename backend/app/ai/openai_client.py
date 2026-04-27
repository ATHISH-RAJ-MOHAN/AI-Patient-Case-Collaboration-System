import os


DEFAULT_OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "30"))
OCR_OPENAI_TIMEOUT_SECONDS = float(os.getenv("OPENAI_OCR_TIMEOUT_SECONDS", "45"))
OPENAI_MAX_RETRIES = int(os.getenv("OPENAI_MAX_RETRIES", "1"))


def create_openai_client(timeout_seconds: float | None = None):
    from openai import OpenAI

    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        timeout=timeout_seconds or DEFAULT_OPENAI_TIMEOUT_SECONDS,
        max_retries=OPENAI_MAX_RETRIES,
    )
