from app.explanations.service import GeneratedExplanation, GeneratedExplanationBatch


class ReviewedProvider:
    name = "test"
    model = "reviewed-fixture"

    async def available(self):
        return True

    async def generate(self, payload):
        explanations = []
        for item in payload:
            fields = {}
            for key, choices in item["reviewed_choices"].items():
                fields[key] = (
                    [alternatives[-1] for alternatives in choices]
                    if key
                    in {
                        "limitations",
                        "recommended_steps",
                        "how_to_check",
                    }
                    else choices[-1]
                )
            explanations.append(GeneratedExplanation(finding_id=item["finding_id"], **fields))
        return GeneratedExplanationBatch(explanations=explanations)
