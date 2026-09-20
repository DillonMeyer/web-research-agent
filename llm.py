"""Small Ollama client."""

import argparse
import os

import requests


def ask_llm(messages, *, model=None, base_url=None, timeout=120, json_mode=False):
    """Send chat history to Ollama and return the assistant's text."""
    model = model or os.environ.get("OLLAMA_MODEL")
    if not model:
        raise ValueError("Set OLLAMA_MODEL to an installed model or pass model=.")
    base_url = base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    if not base_url.startswith(("http://", "https://")):
        raise ValueError("OLLAMA_HOST must start with http:// or https://.")

    body = {"model": model, "messages": messages, "stream": False}
    if json_mode:
        body["format"] = "json"
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/api/chat",
            json=body,
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        status_code = exc.response.status_code if exc.response is not None else "unknown"
        raise RuntimeError(f"Ollama returned HTTP {status_code}: {detail}") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(
            f"Could not complete the request to Ollama at {base_url}. "
            "Check that Ollama is running and the model is available. "
            f"Details: {exc}"
        ) from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("Ollama returned invalid JSON.") from exc

    if not isinstance(payload, dict):
        raise RuntimeError("Ollama returned an unexpected response.")
    if payload.get("error"):
        raise RuntimeError(f"Ollama error: {payload['error']}")
    message = payload.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), str):
        raise RuntimeError("Ollama response is missing assistant text.")
    if not message["content"].strip():
        raise RuntimeError("Ollama returned empty assistant text.")
    return message["content"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test the local Ollama connection.")
    parser.add_argument("prompt", nargs="?", default="Reply with a short greeting.")
    parser.add_argument("--model", help="Installed Ollama model (or set OLLAMA_MODEL).")
    args = parser.parse_args()
    try:
        print(ask_llm([{"role": "user", "content": args.prompt}], model=args.model))
    except (ValueError, RuntimeError) as exc:
        parser.exit(1, f"Error: {exc}\n")
