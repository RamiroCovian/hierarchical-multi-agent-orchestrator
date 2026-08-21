"""Factory de modelos LLM según LLM_PROVIDER."""

import os

from dotenv import load_dotenv

load_dotenv()


def get_llm(temperature: float = 0):
    """Devuelve un chat model según la variable LLM_PROVIDER.

    Valores soportados: openai | anthropic | gemini
    """
    provider = (os.getenv("LLM_PROVIDER") or "openai").strip().lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        kwargs = {}
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            kwargs["api_key"] = api_key

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=temperature,
            **kwargs,
        )

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        kwargs = {}
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            kwargs["api_key"] = api_key

        return ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest"),
            temperature=temperature,
            **kwargs,
        )

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        kwargs = {}
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            kwargs["google_api_key"] = api_key

        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
            temperature=temperature,
            **kwargs,
        )

    raise ValueError(
        f"LLM_PROVIDER no soportado: '{provider}'. "
        "Usá openai, anthropic o gemini."
    )
