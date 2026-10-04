"""Explain reference matching with reviewed choices; model cannot create CVE IDs or URLs."""

import asyncio

import httpx


async def explain_cves(lookup, provider, *, busy=False):
    lookup.ai_source = "fixed"
    lookup.ai_fallback_reason = None
    choices = {
        "title": ["Published vulnerability references", "Understanding these CVE references"],
        "meaning": [lookup.message],
        "why_it_matters": [
            "CVE records describe publicly reported software flaws. A matching record is a lead "
            "to check, not proof of a flaw on this device.",
            "A CVE is a reference number for a reported software problem. These references help "
            "you check whether your device needs an update.",
        ],
        "limitations": [
            [
                "A software fingerprint can be wrong, and vendors may fix problems without "
                "changing the displayed version.",
                "The detected software may be misidentified. A vendor may also have already "
                "fixed the problem in your device's update.",
            ]
        ],
        "recommended_steps": [
            [
                "Check the device maker's update page and compare the affected versions "
                "before making changes.",
                "Open the device maker's support page. Check for updates and whether the "
                "listed problem affects your installed version.",
            ]
        ],
        "how_to_check": [
            [
                "Read the linked CVE and the vendor's advisory. The scan did not test whether "
                "the issue can be exploited.",
                "Use the CVE link to read the details, then check the maker's advice. "
                "This scan has not tried to exploit the problem.",
            ]
        ],
    }
    lookup.explanation = [choices["why_it_matters"][-1]] + [
        choices[field][0][-1] for field in ("limitations", "recommended_steps", "how_to_check")
    ]
    if lookup.status not in {"candidates", "no_matches"} or provider is None or busy:
        lookup.ai_fallback_reason = "scan_busy" if busy else "provider_or_reference_unavailable"
        return lookup
    lookup.ai_model = provider.model
    try:
        async with asyncio.timeout(40):
            batch = await provider.generate(
                [{"finding_id": "cve-context", "reviewed_choices": choices}]
            )
        if len(batch.explanations) != 1:
            raise ValueError("invalid count")
        output = batch.explanations[0].model_dump()
        if output.pop("finding_id") != "cve-context":
            raise ValueError("wrong identity")
        for field, alternatives in choices.items():
            value = output[field]
            if field in {"limitations", "recommended_steps", "how_to_check"}:
                if not isinstance(value, list) or len(value) != len(alternatives):
                    raise ValueError("invalid list")
                if any(
                    item not in allowed for item, allowed in zip(value, alternatives, strict=True)
                ):
                    raise ValueError("invented wording")
            elif value not in alternatives:
                raise ValueError("invented wording")
        lookup.explanation = [
            output["why_it_matters"],
            *output["limitations"],
            *output["recommended_steps"],
            *output["how_to_check"],
        ]
        lookup.ai_source = "ollama"
    except TimeoutError:
        lookup.ai_fallback_reason = "provider_timeout"
    except (ValueError, TypeError, AttributeError, httpx.HTTPError):
        lookup.ai_fallback_reason = "simplification_unavailable_or_invalid"
    return lookup
