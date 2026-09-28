"""Source-bound output schema: exact items, fields, list positions and reviewed choices."""

from itertools import product

FORMAT_VERSION = "1.0.1"


def reviewed_output_schema(findings):
    def tuple_schema(items):
        return {
            "type": "array",
            "prefixItems": items,
            "minItems": len(items),
            "maxItems": len(items),
            # Some local providers reject boolean schemas. The object fallback
            # also constrains providers that do not implement prefixItems.
            "items": {"anyOf": items} if items else {"type": "string"},
        }

    items = []
    for finding in findings:
        fields = {"finding_id": {"type": "string", "const": finding["finding_id"]}}
        for field, choices in finding["reviewed_choices"].items():
            fields[field] = (
                tuple_schema([{"type": "string", "enum": alternatives} for alternatives in choices])
                if field in {"limitations", "recommended_steps", "how_to_check"}
                else {"type": "string", "enum": choices}
            )
            if field in {"limitations", "recommended_steps", "how_to_check"} and len(choices) <= 4:
                # Exact ordered arrays prevent providers with partial tuple-schema
                # support from swapping actions. Bound the schema expansion.
                fields[field] = {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": len(choices),
                    "maxItems": len(choices),
                    "enum": [list(values) for values in product(*choices)],
                }
        items.append(
            {
                "type": "object",
                "properties": fields,
                "required": list(fields),
                "additionalProperties": False,
            }
        )
    return {
        "type": "object",
        "properties": {"explanations": tuple_schema(items)},
        "required": ["explanations"],
        "additionalProperties": False,
    }
