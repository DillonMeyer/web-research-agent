# Operating notes

Local setup, maintenance, and troubleshooting for returning to this project.
For the architecture and project scope, see [README.md](README.md).

## Setup

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) **0.10.5**
and [Ollama](https://ollama.com/download). Python **3.14.5** is pinned;
uv can download it if needed.

Copy `.env.example` to `.env` and set your installed model name. The start script
loads this as shell configuration, overriding matching terminal variables.
Only use a `.env` file you trust. Download models manually with Ollama if needed.

## Run

```sh
./scripts/start.sh --check  # Test a model reply
./scripts/start.sh         # Run the research CLI
./scripts/stop.sh          # Stop Ollama started by start.sh
```

Start synchronizes the Python environment from the lockfile and starts Ollama
if the configured local server isn't responding. It waits briefly for startup
and logs Ollama output to `.runtime/ollama.log`. No environment activation needed.

Ollama stays running after the Python command exits, including after errors.
Use the stop script when done. It checks the saved PID and process start time
before sending a stop signal. An existing Ollama service is reused and must be
stopped manually. Use Ctrl+C to stop the Python CLI. Run one start script at a time.

## Keeping it reproducible

Commit `pyproject.toml`, `uv.lock`, and `.python-version` to Git. Python and uv
versions are pinned, and startup uses `uv sync --locked` to preserve dependency
versions. `.venv`, `.env`, caches, and runtime files are ignored by Git.

Add dependencies deliberately with `uv add PACKAGE`. Upgrade deliberately with
`uv lock --upgrade`, then test. Ollama and model files are managed separately;
websites and external APIs can still change.

Verified on macOS, 2026-09-18: Ollama **0.17.5**, model **qwen3:14b**, digest
`bdbd181c33f2ed1b31c972991882db3cf4d192569092138a7d29e973cd9debe8`.
These are reference versions, not enforced at startup.

## Checks

```sh
uv run --locked python -m unittest discover -s tests -v
./scripts/start.sh --check
```

The first command runs offline checks; the second requests a real model reply.
For an end-to-end check, run a research question and manually review the answer
and cited pages. There is no automated research-quality benchmark yet.

## Troubleshooting

- **Model is missing:** with Ollama running, use `ollama list` to inspect installed
  models. Set `OLLAMA_MODEL` in `.env`, or download it explicitly with
  `ollama pull qwen3:14b`.
- **Slow model response:** each request prints `Waiting for model...` and uses a
  300-second timeout. This is per request, not a total research-run deadline.
  Retry or choose a smaller installed model if needed.
- **Ollama startup fails:** inspect `.runtime/ollama.log`. If you started Ollama
  separately, manage that service manually; the stop script only targets the
  process recorded by this project.
- **Search or page reading fails:** errors are passed back to the model so it can
  choose another source. Rate limits, login walls, PDFs, and JavaScript-heavy
  pages can prevent retrieval.
- **Stopping a run:** Ctrl+C exits Python. Ollama remains running until stopped
  with the stop script or managed manually.

Reports currently print to the terminal and are not saved automatically.
