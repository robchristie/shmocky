# ExecPlan 002: Oracle Sidecar Agent

## Summary

Add a thin Oracle-backed sidecar agent for slow, high-value consultation work such as advice,
second opinions, and deeper analysis. The integration should remain outside the Codex rollout
critical path: a typed backend wrapper invokes the Oracle CLI against a remote signed-in browser
service, returns the final answer, and avoids introducing a second orchestration framework.

## Scope

In scope:

- typed settings for Oracle remote host, token, and execution defaults
- a backend `OracleAgent` wrapper around `npx -y @steipete/oracle`
- one-at-a-time Oracle queries with optional attached file globs
- a minimal API endpoint to submit a prompt and receive the final answer
- a live connectivity smoke test against the configured remote Oracle host
- focused tests and README updates

Out of scope:

- folding Oracle into the Codex event stream
- multi-step Oracle workflows or autonomous retries
- frontend UI beyond the existing backend surface
- streaming Oracle partial output into the browser

## Architecture

Backend:

- `AppSettings` reads Oracle config from `.env`, accepting the existing unprefixed
  `ORACLE_REMOTE_TOKEN` and a default remote host.
- `OracleAgent` builds a CLI invocation using browser engine, remote host/token,
  `--browser-model-strategy current`, and `--write-output` to capture only the final answer.
- The wrapper serializes requests with an async lock because the remote browser target is slow
  and should not be spammed in parallel.
- FastAPI exposes `POST /api/oracle/query` returning the final answer plus execution metadata.

## Milestones

1. Planning and config
   - create this ExecPlan
   - add typed settings and request/response models
2. Oracle wrapper
   - add the `OracleAgent` service
   - capture final answer via `--write-output`
   - protect the remote path with serialized execution
3. API and validation
   - expose a minimal query endpoint
   - add tests for configuration and command construction
   - run a real smoke query against the configured remote service
4. Docs
   - update README with usage and operational caveats

## Validation

- `uv run ruff check .`
- `uv run ty check`
- `uv run --extra dev pytest -q`
- manual smoke: query Oracle through the new wrapper and confirm final answer is returned

## Open Questions

- Whether Oracle should later move from CLI wrapping to `oracle-mcp consult` for a more typed integration.
- Whether the browser UI should expose Oracle prompting directly or keep it as an API-only sidecar for now.

## Progress Notes

- 2026-03-31: Oracle README confirms remote browser clients use `--remote-host/--remote-token`, support `--write-output`, and recommend `--browser-model-strategy current` to preserve the active ChatGPT model selection.
- 2026-03-31: Implemented `OracleAgent`, typed settings, and `POST /api/oracle/query` as a serialized sidecar path outside the Codex event loop.
- 2026-03-31: Live smoke initially failed because Oracle rejects URL-style `https://host:port` values for `--remote-host`; settings now normalize URL input down to `host:port`.
- 2026-03-31: Live smoke passed against the configured remote service with prompt `Reply with exactly: oracle connectivity ok`, returning `oracle connectivity ok` in about 10.6 seconds.
