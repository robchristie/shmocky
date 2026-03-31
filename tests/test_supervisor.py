from __future__ import annotations

from shmocky.supervisor import WorkflowSupervisor


def test_supervisor_extract_json_from_fenced_answer() -> None:
    payload = WorkflowSupervisor._extract_json(
        """```json
{
  "decision": "continue",
  "summary": "Need one more step.",
  "next_prompt": "Run the tests and fix the failure."
}
```"""
    )

    assert '"decision": "continue"' in payload


def test_supervisor_render_template_preserves_literal_json_braces() -> None:
    rendered = WorkflowSupervisor._render_template(
        'Return {"decision":"complete"} and {judge_bundle}',
        judge_bundle="BUNDLE",
    )

    assert rendered == 'Return {"decision":"complete"} and BUNDLE'
