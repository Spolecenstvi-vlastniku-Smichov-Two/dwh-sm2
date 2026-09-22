# DWH-SM2-0001-tests

> Test definition for DWH-SM2-0001 with one test per requirement.

## Design

Verify the founding artifacts: identity document content (vision, StoryPrefix, inheritance), registry registration, and the captured founding knowledge. Tests are epic-root relative (run from the story worktree); registry assertions target the instance `ahabase.yaml` via `$HOME` because the registry lives outside the Epic.

## Definition

```yaml
tests:
  - name: R1_identity_document_with_vision
    description: identity declares Epic type with a filled vision and no TODO markers
    command: |
      test -f _grid4d/story/DWH-SM2.md &&
      grep -qF '**Type:** Epic' _grid4d/story/DWH-SM2.md &&
      grep -q '## Vision' _grid4d/story/DWH-SM2.md &&
      grep -q '730540-2' _grid4d/story/DWH-SM2.md &&
      ! grep -q 'TODO' _grid4d/story/DWH-SM2.md
    expect:
      exit_code: 0
  - name: R2_storyprefix_canonically_declared
    description: identity document carries the canonical StoryPrefix field
    command: |
      grep -qF '**StoryPrefix:** DWH-SM2-' _grid4d/story/DWH-SM2.md
    expect:
      exit_code: 0
  - name: R3_epic_registered_in_registry
    description: instance registry maps the prefix and holds the epic entry with clean remote
    command: |
      grep -q 'DWH-SM2: dwh-sm2' "$HOME/ahabase/_config/ahabase.yaml" &&
      grep -q 'github.com/Spolecenstvi-vlastniku-Smichov-Two/dwh-sm2' "$HOME/ahabase/_config/ahabase.yaml"
    expect:
      exit_code: 0
  - name: R4_inheritance_declared
    description: identity declares EVOLUCEAN as the parent epic
    command: |
      grep -qF '**Inherits:** EVOLUCEAN' _grid4d/story/DWH-SM2.md
    expect:
      exit_code: 0
  - name: R5_founding_knowledge_logged
    description: founding procedure idea and all founding issue documents exist
    command: |
      test -f _grid4d/idea/epic-founding-procedure.md &&
      test -f _grid4d/issue/story-create-cross-epic-mint-proceeds.md &&
      test -f _grid4d/issue/no-cli-cleanup-for-wrong-mint.md &&
      test -f _grid4d/issue/epic-init-inherits-root-default.md &&
      test -f _grid4d/issue/epic-init-identity-missing-storyprefix.md
    expect:
      exit_code: 0
```

## Execution

| Test | Result | Date |
|------|--------|------|
| R1_identity_document_with_vision | ✅ | 2026-09-22 |
| R2_storyprefix_canonically_declared | ✅ | 2026-09-22 |
| R3_epic_registered_in_registry | ✅ | 2026-09-22 |
| R4_inheritance_declared | ✅ | 2026-09-22 |
| R5_founding_knowledge_logged | ✅ | 2026-09-22 |

## Related

- [DWH-SM2-0001](DWH-SM2-0001) - Parent story

---
## _behavior

validation:
  required_sections: [Design, Definition, Execution]
  definition_format: yaml_code_block
