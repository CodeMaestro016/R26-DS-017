"""Panel display reads saved backend values and rejects corrupted summaries."""
import hashlib
import inspect
import json
from socialmind_drive_showcase.services import targeted_validation_reader as reader

def test_panel_reader_preserves_metrics_without_frontend_recalculation(tmp_path):
    payload = dict(schema_version=1, evidence_classification="TARGETED_PANEL_VALIDATION",
        cases=[dict(case_id="PV-04", classification="SAFE_DEGRADATION", metrics=dict(mean_waiting_time_seconds=17.25))])
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    path = tmp_path / "panel_summary.json"
    path.write_text(raw)
    path.with_name("panel_summary.sha256.json").write_text(json.dumps(dict(payload_hash=hashlib.sha256(raw.encode()).hexdigest())))
    result = reader.read_targeted_validation(path)
    assert result["available"] and result["payload"] == payload
    path.write_text(raw.replace("17.25", "0.0"))
    assert not reader.read_targeted_validation(path)["available"]
    assert "targeted_validation.runner" not in inspect.getsource(reader)

def test_missing_panel_outputs_stay_unavailable(tmp_path):
    assert not reader.read_targeted_validation(tmp_path / "missing.json")["available"]
