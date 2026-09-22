# Implementation Epic Blueprint Missing Template

> implementation-epic-blueprint.md lacks the Template section required by blueprint-blueprint

**Status:** open
**Stories:** DWH-SM2-0001

## Problem

The PostToolUse hook flags every read of `evolucean/_grid4d/implementation/implementation-epic-blueprint.md`:

```
Document type: blueprint
Blueprint: blueprint-blueprint
  ✗ Missing required sections: Template
```

The document is a type-blueprint that other documents are validated against, yet it does not satisfy its own type's required sections.

## Root Cause

The blueprint predates the `## Template` requirement of blueprint-blueprint (or the requirement was added without a migration pass over existing blueprints).

## Occurrences

| Occurred   | Story                 | Manifestation                                                                 |
| ---------- | --------------------- | ----------------------------------------------------------------------------- |
| 2026-09-22 | DWH-SM2-0001 founding | Read while preparing the dwh-sm2 identity document; hook flagged the missing section. |
| 2026-09-22 | DWH-SM2-0001 founding | `implementation-epic-inheritance-blueprint.md` flagged with the same class: missing `Template` + `Structure`. The audit-pass note above covers it. |

## Notes

evolucean-owned document; fix belongs to an evolucean docs story. Likely siblings: other `*-blueprint.md` documents missing `## Template` - worth a doctor/audit pass instead of a one-off edit.
