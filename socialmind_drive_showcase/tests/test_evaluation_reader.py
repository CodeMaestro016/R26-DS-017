import inspect
import json
from socialmind_drive_showcase.services import evaluation_reader

def test_reader_missing_and_invalid_outputs(tmp_path):
    assert not evaluation_reader.read_evaluation(tmp_path / "missing.json")["available"]
    path = tmp_path / "aggregate.json"
    path.write_text("{}")
    assert not evaluation_reader.read_evaluation(path)["available"]

def test_reader_returns_backend_values_without_writing_or_recomputing(tmp_path):
    path = tmp_path / "aggregate.json"
    payload = {"schema_version":1,"groups":[{"metrics":{"completion_rate":{"mean":.37}}}]}
    path.write_text(json.dumps(payload))
    before = path.read_bytes()
    result = evaluation_reader.read_evaluation(path)
    assert result["payload"] == payload and path.read_bytes() == before
    source = inspect.getsource(evaluation_reader)
    assert "post_training_evaluation" not in source.replace("results/post_training_evaluation", "")
    assert "write_text" not in source and "subprocess" not in source

def test_quantitative_route_and_qualitative_disclaimer_preserved():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    assert "/component/right-of-way/evaluation" in (root / "app.py").read_text()
    assert "QUALITATIVE PRESENTATION ONLY" in (root / "pages/component2_results.py").read_text()
    live = (root / "pages/component2_live_view.py").read_text(encoding="utf-8")
    assert "PLANNER READY / BLOCKED" not in live
    assert "EGO-LOCAL EXECUTION" in live
