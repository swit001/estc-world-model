import json
import subprocess
import sys
from pathlib import Path

import pytest

from estc_world_model.schema import verdict_schema, world_schema


class TestWorldSchema:
    def test_returns_dict(self):
        schema = world_schema()
        assert isinstance(schema, dict)

    def test_has_title(self):
        schema = world_schema()
        assert "title" in schema

    def test_transitions_is_required(self):
        schema = world_schema()
        assert "transitions" in schema.get("required", [])

    def test_transitions_property_defined(self):
        schema = world_schema()
        props = schema.get("properties", {})
        assert "transitions" in props

    def test_constraints_property_defined(self):
        schema = world_schema()
        props = schema.get("properties", {})
        assert "constraints" in props

    def test_world_meta_property_defined(self):
        schema = world_schema()
        props = schema.get("properties", {})
        assert "world" in props

    def test_is_json_serializable(self):
        schema = world_schema()
        dumped = json.dumps(schema)
        assert isinstance(dumped, str)


class TestVerdictSchema:
    def test_returns_dict(self):
        schema = verdict_schema()
        assert isinstance(schema, dict)

    def test_has_title(self):
        schema = verdict_schema()
        assert "title" in schema

    def test_status_is_required(self):
        schema = verdict_schema()
        assert "status" in schema.get("required", [])

    def test_status_property_defined(self):
        schema = verdict_schema()
        props = schema.get("properties", {})
        assert "status" in props

    def test_guard_result_property_defined(self):
        schema = verdict_schema()
        props = schema.get("properties", {})
        assert "guard_result" in props

    def test_committed_state_property_defined(self):
        schema = verdict_schema()
        props = schema.get("properties", {})
        assert "committed_state" in props

    def test_is_json_serializable(self):
        schema = verdict_schema()
        dumped = json.dumps(schema)
        assert isinstance(dumped, str)


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "estc_world_model.cli"] + args,
        capture_output=True,
        text=True,
    )


class TestSchemaCommand:
    def test_world_schema_to_stdout(self):
        result = _run(["schema"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
        assert "properties" in data

    def test_verdict_schema_to_stdout(self):
        result = _run(["schema", "--verdict"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, dict)
        assert "properties" in data
        assert "status" in data["properties"]

    def test_all_schema_to_stdout(self):
        result = _run(["schema", "--all"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "world" in data
        assert "verdict" in data
        assert isinstance(data["world"], dict)
        assert isinstance(data["verdict"], dict)

    def test_world_schema_to_file(self, tmp_path):
        out = tmp_path / "world.schema.json"
        result = _run(["schema", "--out", str(out)])
        assert result.returncode == 0
        assert out.exists()
        data = json.loads(out.read_text())
        assert isinstance(data, dict)

    def test_verdict_schema_to_file(self, tmp_path):
        out = tmp_path / "verdict.schema.json"
        result = _run(["schema", "--verdict", "--out", str(out)])
        assert result.returncode == 0
        assert out.exists()
        data = json.loads(out.read_text())
        assert "status" in data.get("properties", {})

    def test_all_schema_to_directory(self, tmp_path):
        result = _run(["schema", "--all", "--out", str(tmp_path)])
        assert result.returncode == 0
        world_file = tmp_path / "world.schema.json"
        verdict_file = tmp_path / "verdict.schema.json"
        assert world_file.exists()
        assert verdict_file.exists()
        assert isinstance(json.loads(world_file.read_text()), dict)
        assert isinstance(json.loads(verdict_file.read_text()), dict)

    def test_all_creates_output_directory(self, tmp_path):
        out_dir = tmp_path / "nested" / "schemas"
        result = _run(["schema", "--all", "--out", str(out_dir)])
        assert result.returncode == 0
        assert (out_dir / "world.schema.json").exists()
        assert (out_dir / "verdict.schema.json").exists()
