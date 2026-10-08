# Identity Declaration vs Tooling Divergence

> The identity concept says the identity file is the only registration, but the validation tooling still keys off the legacy yaml - canonically registered subepics get zero doctor coverage.

**Status:** open (fix belongs to EVOLUCEAN)
**Found in:** DWH-SM2-APP-0006 (2026-10-08, Human-directed identity-concept review)

## Problem

[ontology-identity-system-blueprint](ontology-identity-system-blueprint) (evolucean-body) declares the canonical model: an epic or subepic "MUST declare its identity once in its identity file (def-doc); creating that file is the registration - **no separate configuration exists**". [evolucean-story-identity-pattern](evolucean-story-identity-pattern) agrees: definition documents are the canonical source; yaml `story_prefixes` / registry entries are legacy fallback during retirement.

The instruments contradict the declared model:

- `knowledge-usage doctor` iterates subepics from the **yaml registry only** (`config_identity.py`: `for sub_name, sub_config in epic_config.get("subepics", {}).items()`) - the legacy fallback drives which def-docs get validated. A subepic registered the canonical way (identity file present, no yaml entry - the intended post-retirement state) is **never examined**: `dwh-sm2-app` shipped stories 0004-0006 this way and doctor reported `0 errors, 0 warnings` throughout. Doctor's silence means "not checked", not "consistent".
- The same yaml-first keying sits under `_epic_setting` overrides (branch/release/merge per subepic read from `subepics:` config) - legacy config remains a live input, not just a fallback display.

Story work must rest on clear subepic identification; today the guarantee holds only because mint-time derivation happens to agree with the def-doc, not because anything validates it.

## Solution Direction (EVOLUCEAN side)

Flip the iteration source: doctor should scan the **filesystem** (`_grid4d/subepic/*/`) for def-docs (missing identity file → warning, missing `StoryPrefix` → error) and use the def-doc scan as the driver, with yaml entries checked only for retirement-era disagreement. That inverts the current trust direction to match the declared concept. Sibling finding: issue `dwh-sm2-app-resume-binds-calling-tree` - the session-level identity covers which story a session binds but not which tree anchors the work.

## Occurrences

| Date | Story | Signature |
|------|-------|-----------|
| 2026-10-08 | DWH-SM2-APP-0006 | dwh-sm2-app: def-doc present, no yaml entry, doctor silent; `config_identity.py` iterates `epic_config.get("subepics", {})` |
