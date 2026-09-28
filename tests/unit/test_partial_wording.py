import pytest
from app.explanations.format import reviewed_output_schema
from app.explanations.service import ExplanationService
from tests.unit.test_explanations import FakeProvider, make_stored_scan


def test_output_schema_fixes_ids_choices_and_list_lengths():
    schema = reviewed_output_schema(
        [
            {
                "finding_id": "f1",
                "reviewed_choices": {
                    "title": ["Original", "Plain"],
                    "meaning": ["A feature answered."],
                    "why_it_matters": ["Review it."],
                    "limitations": [],
                    "recommended_steps": [["Ask its owner."], ["Read the manual."]],
                    "how_to_check": [],
                },
            }
        ]
    )
    array = schema["properties"]["explanations"]
    assert array["minItems"] == array["maxItems"] == 1
    fields = array["prefixItems"][0]["properties"]
    assert fields["finding_id"]["const"] == "f1"
    assert fields["title"]["enum"] == ["Original", "Plain"]
    steps = fields["recommended_steps"]
    assert steps["minItems"] == steps["maxItems"] == 2
    assert steps["enum"] == [["Ask its owner.", "Read the manual."]]
    assert isinstance(steps["items"], dict)


@pytest.mark.asyncio
async def test_partial_fields_retry_preserves_accepted_text_across_requests(tmp_path):
    store, document = await make_stored_scan(tmp_path)

    class PartialProvider(FakeProvider):
        async def generate(self, payload):
            batch = await super().generate(payload)
            for item in batch.explanations:
                if item.finding_id == document.findings[0].finding_id:
                    if len(self.calls) <= 2:
                        item.recommended_steps = []
                    else:
                        # A retry may not undo a previously accepted simplification.
                        item.meaning = document.findings[0].fixed_explanation.meaning
            return batch

    provider = PartialProvider()
    service = ExplanationService(store, provider)
    partial = await service.explain_scan(document.scan_id)
    assert partial.analysis_status == "failed"
    assert partial.explanations[0].status == "ready"
    assert partial.explanations[0].rejected_fields
    accepted = partial.explanations[0].content.meaning
    complete = await service.explain_scan(document.scan_id)
    assert complete.analysis_status == "ready"
    assert not complete.explanations[0].rejected_fields
    assert complete.explanations[0].content.meaning == accepted
    assert len(provider.calls) == 3
    assert len(provider.calls[-1]) == 1
    assert provider.calls[-1][0]["reviewed_choices"]["meaning"] == [accepted]
    assert complete.findings == document.findings
    assert complete.services == document.services
    await service.explain_scan(document.scan_id)
    assert len(provider.calls) == 3


@pytest.mark.asyncio
async def test_partial_list_retry_does_not_overwrite_accepted_elements(tmp_path):
    store, document = await make_stored_scan(tmp_path)

    class PartialListProvider(FakeProvider):
        async def generate(self, payload):
            batch = await super().generate(payload)
            for item, source in zip(batch.explanations, payload, strict=True):
                item.recommended_steps = [
                    c[-1] for c in source["reviewed_choices"]["recommended_steps"]
                ]
                if item.finding_id == document.findings[0].finding_id:
                    if len(self.calls) == 1:
                        item.recommended_steps[0] = "Delete everything on the device."
                    else:
                        item.recommended_steps[1] = "Delete everything on the device."
            return batch

    provider = PartialListProvider()
    result = await ExplanationService(store, provider).explain_scan(document.scan_id)
    assert result.analysis_status == "ready"
    assert not result.explanations[0].rejected_fields
    assert "Delete" not in " ".join(result.explanations[0].content.recommended_steps)
    assert len(provider.calls) == 2
