"""UI removal must not silently overwrite omitted legacy JSON settings."""

import pytest
from app.schemas.settings import SettingsUpdate
from app.storage.json_store import JsonStore


@pytest.mark.parametrize("legacy_choice", [False, True])
def test_saving_visible_settings_preserves_omitted_pihole_choice(tmp_path, legacy_choice):
    store = JsonStore(tmp_path)
    saved = store._update_settings(
        SettingsUpdate(expected_revision=1, pihole_enabled=legacy_choice), 1
    )
    update = SettingsUpdate(expected_revision=saved.revision, retain_raw_xml=True)
    assert "pihole_enabled" not in update.model_fields_set
    result = store._update_settings(update, saved.revision)
    assert result.pihole_enabled is legacy_choice
    assert result.retain_raw_xml is True
