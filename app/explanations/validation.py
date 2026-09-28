"""Pure source-bound AI wording validation; no provider, storage or network access."""

import re

from .wording import wording_choices


def validated_line(
    original: str,
    candidate: str | None,
    *,
    field: str,
    rule_id: str,
    reviewed_choices: list[str] | None = None,
) -> tuple[str, bool]:
    if candidate is None or candidate.strip().casefold() == original.strip().casefold():
        return original, False
    # Exact source-bound alternatives are the acceptance boundary. Regex checks
    # below explain rejections; they are not proof of semantic equivalence.
    if candidate.strip() in (reviewed_choices or wording_choices(original))[1:]:
        return candidate.strip(), True
    source = original.casefold()
    output = candidate.casefold()
    max_words = 16 if field == "title" else 35
    if len(candidate.split()) > max_words or len(candidate.split()) > len(original.split()) + 8:
        raise ValueError("rewrite_too_long")
    if any(not char.isprintable() for char in candidate):
        raise ValueError("invalid_provider_response")
    disallowed = (
        "anyone",
        "everyone",
        "others",
        "strangers",
        "any information",
        "all information",
        "everything sent",
        "attacker",
        "hacker",
        "completely safe",
        "definitely safe",
        "guaranteed safe",
        "has been hacked",
        "is hacked",
        "is compromised",
        "no risk",
        "not secure",
        "unsafe",
        "vulnerable",
        "exposed",
        "verified explanation",
        "original text",
        "input data",
        "that claim",
    )
    if any(phrase in output and phrase not in source for phrase in disallowed):
        raise ValueError("unsupported_absolute_claim")
    guarded_terms = (
        "someone",
        "password",
        "credential",
        "malware",
        "internet",
        "sensitive",
        "compromised",
        "hacked",
        "exploit",
        "crack",
        "cve",
        "cipher",
        "packet",
        "protocol",
        "tls",
        "ssl",
    )
    if any(
        re.search(rf"\b{re.escape(term)}\b", output)
        and not re.search(rf"\b{re.escape(term)}\b", source)
        for term in guarded_terms
    ):
        raise ValueError("unsupported_security_concept")
    if re.search(r"\b(may|might|could|can|normally|usually|possibly)\b", source):
        if not re.search(
            r"\b(may|might|could|can|normally|usually|possibly|typically|often|generally)\b",
            output,
        ):
            raise ValueError("qualifier_removed")
    if re.search(r"\b(did not|does not|was not|were not|not checked|without|no)\b", source):
        if not re.search(r"\b(not|never|without|no|didn't|doesn't|cannot|can't)\b", output):
            raise ValueError("limitation_removed")
    for source_marker, output_pattern in (
        (r"\bonly\b", r"\b(only|just)\b"),
        (r"\bif\b", r"\b(if|when)\b"),
        (r"\bbefore\b", r"\b(before|first|prior)\b"),
        (r"\bolder\b", r"\b(older|old|legacy)\b"),
    ):
        if re.search(source_marker, source) and not re.search(output_pattern, output):
            raise ValueError("condition_removed")
    if re.search(r"\b(?:this|the) scan did not\b", source):
        if not (
            re.search(r"\b(scan|we|our test|checks)\b", output)
            and re.search(r"\b(not|never|didn't|wasn't|cannot|can't|untested)\b", output)
            and re.search(
                r"\b(check|checked|test|tested|try|tried|verify|verified|confirm|confirmed|tell|know)\b",
                output,
            )
        ):
            raise ValueError("scan_limitation_removed")
        required_topics = {
            "R01": (r"\b(sign|login|log-in)\b", r"\b(use|access|who)\b"),
            "R02": (r"\b(protected|alternative|encrypt)\b",),
            "R03": (r"\b(redirect|https|page)\b",),
            "R04": (r"\b(sign|access|permission|rule)\b",),
            "R05": (r"\b(folder|permission)\b",),
            "R06": (r"\b(connect|message|protected|encrypt)\b",),
        }
        if any(not re.search(pattern, output) for pattern in required_topics.get(rule_id, ())):
            raise ValueError("scan_limitation_changed")
    if re.findall(r"\b\d+\b", source) != re.findall(r"\b\d+\b", output):
        raise ValueError("number_changed")
    if field == "title":
        anchors = {
            "R01": r"\btelnet\b",
            "R02": r"\bftp\b",
            "R03": r"\bhttp\b",
            "R04": r"\b(remote|desktop|control)\b",
            "R05": r"\b(file|sharing|folder)\b",
            "R06": r"\bmqtt\b",
            "R07": r"\b(connection|port)\b",
        }
        anchor = anchors.get(rule_id)
        if anchor and not re.search(anchor, output):
            raise ValueError("service_name_removed")
    if field in {"recommended_steps", "how_to_check"}:
        risky_new_commands = ("disable", "delete", "reset", "install", "update", "open", "off")
        if any(
            re.search(rf"\b{word}\b", output) and not re.search(rf"\b{word}\b", source)
            for word in risky_new_commands
        ):
            raise ValueError("new_action")
        allowed_starts = {
            "if",
            "when",
            "first",
            "check",
            "review",
            "look",
            "confirm",
            "verify",
            "compare",
            "ask",
            "find",
            "limit",
            "restrict",
            "use",
            "choose",
            "make",
        }
        if candidate.split()[0].strip(".!,:").casefold() not in allowed_starts:
            raise ValueError("new_action")
        if re.search(r"\bask\b", source) and not re.search(r"\b(ask|contact)\b", output):
            raise ValueError("action_precaution_removed")
    raise ValueError("unreviewed_rewrite")
