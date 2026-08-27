## Objective

<!-- What outcome does this PR deliver? -->

## Scope

<!-- What is intentionally included? -->

## Non-goals

<!-- What is intentionally excluded? -->

## Decisions / ADRs

<!-- Link or name relevant ADRs. Do not represent proposals as accepted decisions. -->

## Validation

Run the local quality preflight before commit/push when Python or tests change. This avoids using CI as the first lint feedback loop; Ruff enforces the repository line-length limit (`88`) and other configured rules.

```bash
uv run ruff check .
uv run ty check
uv run pytest -q
```

- [ ] Local quality preflight completed before commit/push
- [ ] Ruff/static checks green
- [ ] Type checks green (when configured/applicable)
- [ ] Unit tests green
- [ ] Integration tests green (when applicable)
- [ ] Build/package validation green (when applicable)
- [ ] DAB validation/runtime smoke completed (when applicable)

Commands/evidence:

```text
<commands or CI checks>
```

## Data / Governance impact

- Schema/contract impact: None / describe
- Table lifecycle/migration impact: None / describe
- Governed tags / ABAC impact: None / describe
- Environment impact (`dev`/`stg`/`prd`): None / describe

## Documentation

- [ ] New/materially changed public APIs have useful docstrings
- [ ] Feature docs reflect actual implementation
- [ ] ADRs updated/accepted where required
- [ ] Developer/operator instructions updated where required
- [ ] Reusable convention changes reflected in `engineering-standards.md`

## Definition of Done

- [ ] `docs/development/definition-of-done.md` reviewed
- [ ] No hidden blocker/high-severity known defect
- [ ] No invented governance facts, requirements, owners or deadlines
- [ ] No unrelated scope expansion

## Follow-ups / backlog

<!-- Capture deferred work instead of silently expanding this PR. -->
