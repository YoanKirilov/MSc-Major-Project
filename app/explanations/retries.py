"""Preserve accepted wording while retrying only unresolved fields."""

from copy import deepcopy


def needs_retry(record):
    return bool(record.rejected_fields) or (
        record.status != "ready" and record.fallback_reason != "not_simpler"
    )


def retained_values(record, finding):
    return {
        "title": record.display_title or finding.title,
        "meaning": record.content.meaning,
        "why_it_matters": record.content.why_it_matters,
        "limitations": record.display_limitations or finding.limitations,
        "recommended_steps": record.content.recommended_steps,
        "how_to_check": record.content.how_to_check,
    }


def field_locked(record, field, index=None):
    if not record or not record.rejected_fields:
        return False
    return field not in record.rejected_fields and (
        index is None or f"{field}[{index}]" not in record.rejected_fields
    )


def retry_payload(payload, record, finding):
    if not record or not record.rejected_fields:
        return payload
    result = deepcopy(payload)
    retained = retained_values(record, finding)
    for field, choices in result["reviewed_choices"].items():
        if isinstance(retained[field], list):
            for index in range(len(choices)):
                if field_locked(record, field, index):
                    choices[index] = [retained[field][index]]
        elif field_locked(record, field):
            result["reviewed_choices"][field] = [retained[field]]
    return result
