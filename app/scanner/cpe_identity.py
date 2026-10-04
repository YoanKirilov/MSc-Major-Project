"""Conservative NVD dictionary resolution, never generated aliases or port guesses."""

CPE_API = "https://services.nvd.nist.gov/rest/json/cpes/2.0"


async def resolve_identity(query, fetch):
    from app.scanner.cve import application_cpe

    fields = query.split(":")

    def compatible(name):
        value = application_cpe(name)
        if not value:
            return None
        parts = value.split(":")
        if parts[2] != fields[2] or parts[4:6] != fields[4:6]:
            return None
        if any(
            original != "*" and original != part
            for original, part in zip(fields[6:], parts[6:], strict=True)
        ):
            return None
        return value

    async def products(pattern):
        data = await fetch(CPE_API, {"cpeMatchString": pattern, "resultsPerPage": 20})
        rows = data["products"]
        total = data["totalResults"]
        if type(total) is not int or not isinstance(rows, list) or total != len(rows) or total > 20:
            raise ValueError("incomplete product dictionary page")
        return [row["cpe"] for row in rows]

    rows = await products(query)
    method = "exact_dictionary"
    if not rows:
        pattern = list(fields)
        pattern[3] = "*"
        rows = await products(":".join(pattern))
        method = "unique_product_version_candidate"
    if not rows:
        return None, "unresolved", []
    resolved = set()
    provenance = set()
    for row in rows:
        original = compatible(row.get("cpeName", ""))
        if not original:
            return None, "unresolved", []
        provenance.add(original)
        if row.get("deprecated") is True:
            replacements = row.get("deprecatedBy", [])
            if len(replacements) != 1:
                return None, "ambiguous", sorted(provenance)
            replacement = compatible(replacements[0].get("cpeName", ""))
            if not replacement or replacement == original:
                return None, "unresolved", sorted(provenance)
            # Verify the replacement exists and is current. Do not chase unbounded chains.
            current = await products(replacement)
            if (
                len(current) != 1
                or current[0].get("deprecated") is not False
                or current[0].get("cpeName") != replacement
            ):
                return None, "unresolved", sorted(provenance)
            resolved.add(replacement)
            provenance.add(replacement)
            if method == "exact_dictionary":
                method = "explicit_deprecation"
        elif row.get("deprecated") is False:
            resolved.add(original)
        else:
            return None, "unresolved", sorted(provenance)
    if len(resolved) != 1:
        return None, "ambiguous", sorted(provenance)
    return next(iter(resolved)), method, sorted(provenance)
