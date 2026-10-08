# DWH-SM2-0004-tests

> Test definition for DWH-SM2-0004 with one test per requirement.

## Design

Structural verification of the founding: the identity file is checked verbatim for the
blueprint-required fields (type, inheritance, prefix, Vision, Scope) and for the declared
first-story direction. Recognition is checked through the CLI prefix resolver directly -
the SubEpics projection regenerates in the main tree only after merge, so the test calls
`is_story_file` on a `DWH-SM2-APP-NNN` filename against the worktree's `_grid4d/`; the
identity-file StoryPrefix is the authoritative declaration (no yaml entry involved).
Tests are worktree-root relative, POSIX sh, run with the CLI venv on PATH.

## Definition

```yaml
tests:
  - name: R1_identity_file_blueprint_fields
    description: subepic identity file exists and carries the blueprint-required declarations
    command: |
      test -f _grid4d/subepic/dwh-sm2-app/story/DWH-SM2-APP.md &&
      grep -qF '**Type:** SubEpic' _grid4d/subepic/dwh-sm2-app/story/DWH-SM2-APP.md &&
      grep -qF '**Inherits:** dwh-sm2' _grid4d/subepic/dwh-sm2-app/story/DWH-SM2-APP.md &&
      grep -qF '**StoryPrefix:** DWH-SM2-APP-' _grid4d/subepic/dwh-sm2-app/story/DWH-SM2-APP.md &&
      grep -q '^## Vision' _grid4d/subepic/dwh-sm2-app/story/DWH-SM2-APP.md &&
      grep -q '^## Scope' _grid4d/subepic/dwh-sm2-app/story/DWH-SM2-APP.md
    expect:
      exit_code: 0
  - name: R2_prefix_resolution_recognizes_subepic
    description: resolver classifies a DWH-SM2-APP-NNN filename as a story file via the identity declaration
    command: |
      PYTHONPATH="$HOME/ahabase/evolucean/knowledge-usage-cli/src" python -c "import sys; from pathlib import Path; from knowledge_usage_cli.status import is_story_file; sys.exit(0 if is_story_file('DWH-SM2-APP-001.md', Path('_grid4d')) else 1)"
    expect:
      exit_code: 0
  - name: R3_first_story_direction_declared
    description: identity file names the full application audit as the Human-set first story
    command: |
      grep -q 'DWH-SM2-APP-001' _grid4d/subepic/dwh-sm2-app/story/DWH-SM2-APP.md &&
      grep -q 'full application audit' _grid4d/subepic/dwh-sm2-app/story/DWH-SM2-APP.md
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_identity_file_blueprint_fields | ✅ | 2026-10-08 |
| R2_prefix_resolution_recognizes_subepic | ✅ | 2026-10-08 |
| R3_first_story_direction_declared | ✅ | 2026-10-08 |

## Related

- [DWH-SM2-0004](DWH-SM2-0004) - Parent story
- [DWH-SM2-APP](DWH-SM2-APP) - Founded SubEpic identity

---
## _behavior

validation:
  required_sections: [Design, Definition, Execution]
  definition_format: yaml_code_block
