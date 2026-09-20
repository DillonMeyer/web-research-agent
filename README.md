# Web Research Agent

A Python CLI research agent in progress. Model decisions are implemented: the model chooses search, fetch, or finish,
and Python validates the choice. Search and page-fetch tools now use the live web. Reports are printed to the
terminal; citation support still needs human review.

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

## Decision loop

`decisions.py` sends the question, action history, and collected evidence to the
model using JSON mode. Python validates the action and required argument, with
one retry for malformed output. `agent.py` executes the tool and saves its result
for the next decision. Finish returns the model's Markdown answer; citations
are prompted but their factual support is not yet checked automatically.

Run the offline checks with:

```sh
uv run --locked python -m unittest discover -s tests -v
```

## Web tools

Search uses [DDGS](https://github.com/deedy5/ddgs) with its DuckDuckGo backend
(no API key). Page reading uses [Trafilatura](https://trafilatura.readthedocs.io/)
to extract article text. Versions and indirect dependencies are saved in `uv.lock`.
Search returns up to five results; pages have a 2 MB download limit and a
12,000-character text limit. Failures are returned to the model so it can try
another source. PDF files and pages requiring JavaScript or login are unsupported.
Search providers can rate-limit requests; a locked dependency cannot prevent that.
