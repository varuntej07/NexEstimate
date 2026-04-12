# Workflow Orchestration

## 1. Plan Mode Default
- Enter plan mode for ANY non-trivial task (2+ steps) and have a bird's eye view of the changes you're about to make.
- If something goes sideways, STOP. fetch latest documentation and re-plan immediately
- Use plan mode for verification steps, not just building
- Write detailed specs upfront or ask clarifying questions to reduce ambiguity

## 2. Subagent Strategy
- Use subagents liberally to keep main context window clean
- Offload research, exploration, and parallel analysis
- For complex problems, throw more compute at it via subagents
- One task per subagent for focused execution

## 3. Self-Improvement Loop
- After ANY correction and major bug: update `problems-faced.txt`
- Write rules for yourself that prevent the same mistakes
- Ruthlessly iterate on these lessons until mistake-free (this is the most important rule)
- Review lessons at session start for relevant projects

## 4. Verification Before Done
- Never mark a task complete without proving it works (this is the second most important rule)
- Diff behavior between main and your changes when reviewing
- Ask yourself: "Would a staff engineer approve this?"
- Run tests, check logs, demonstrate correctness

## 5. Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a simpler way?"
- If a fix feels hacky: "Knowing everything I know now, is this right?"
- Skip this for simple, obvious fixes — don't over-engineer
- Challenge your own work before presenting it

## 6. Autonomous Bug Fixing
- When given a bug report: Give the plan and get approval, then fix it.
- Point at logs, errors, failing tests - then resolve them
- Zero context switching required from the user
- Go fix failing CI tests without being told how

---

# Core Principles

- **Simplicity First**: Make every change as simple as possible
- **No Laziness**: Find root causes. No temporary fixes
- **Minimal Impact**: Changes should only touch what's necessary

---

# Architecture Notes

## Three-File Backend Pattern

- `api/core.py` — shared business logic. Config constants (`RAPIDAPI_KEY/HOST`, `ALLOWED_ORIGIN`, `RATE_LIMIT`, `TIMEOUTS`), input validation (`_ADDRESS_RE`, `_ADDRESS_MAX_LEN`), structured logging (`logger`, `_hash_addr`), Pydantic models (`ZestimateRange`, `PropertyEstimate`), `_fetch_with_retry`, `_parse_property`, and `get_estimate_handler(address, client)`. 
**All logic changes go here once.**
- `main.py` — local dev only. Owns the persistent `httpx.AsyncClient` lifespan and SPA static file serving. Delegates `/api/estimate` to `get_estimate_handler`.
- `api/index.py` — Vercel serverless. Creates a fresh `httpx.AsyncClient` per invocation (no lifespan support). Delegates `/api/estimate` to `get_estimate_handler`. No static file serving (Vercel handles that).