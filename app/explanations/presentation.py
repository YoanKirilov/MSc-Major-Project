"""Read-only beginner display choices; do not alter evidence or claim new AI output."""

from .report import report_input
from .wording import wording_choices


def plain_finding(finding):
    return {
        "title": wording_choices(finding.title)[-1],
        "limitations": [wording_choices(line)[-1] for line in finding.limitations],
        "content": {
            "meaning": wording_choices(finding.fixed_explanation.meaning)[-1],
            "why_it_matters": wording_choices(finding.fixed_explanation.why_it_matters)[-1],
            "recommended_steps": [wording_choices(action.text)[-1] for action in finding.actions],
            "how_to_check": [
                wording_choices(action.verification)[-1] for action in finding.actions
            ],
        },
    }


def plain_report(document):
    _, payload = report_input(document)
    choices = payload["reviewed_choices"]
    return {
        "limitations": [options[-1] for options in choices["limitations"]],
        "content": {
            key: [options[-1] for options in choices[key]]
            if key in {"recommended_steps", "how_to_check"}
            else choices[key][-1]
            for key in ("meaning", "why_it_matters", "recommended_steps", "how_to_check")
        },
    }
