import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

COMMERCE_YAML = Path(__file__).parent.parent / "examples" / "commerce_refund" / "world.yaml"
MARKETING_YAML = Path(__file__).parent.parent / "examples" / "marketing_budget" / "world.yaml"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "estc_world_model.cli"] + args,
        capture_output=True,
        text=True,
    )


class TestValidateCommand:
    def test_valid_commerce_world(self):
        result = _run(["validate", str(COMMERCE_YAML)])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid"] is True
        assert data["world"] == "Commerce Refund World"
        assert data["entities"] == 0
        assert data["transitions"] == 3
        assert data["constraints"] == 3

    def test_valid_marketing_world(self):
        result = _run(["validate", str(MARKETING_YAML)])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["valid"] is True
        assert data["entities"] == 0

    def test_output_is_single_line_json(self):
        result = _run(["validate", str(COMMERCE_YAML)])
        assert result.returncode == 0
        lines = result.stdout.strip().splitlines()
        assert len(lines) == 1
        json.loads(lines[0])

    def test_file_not_found(self):
        result = _run(["validate", "nonexistent.yaml"])
        assert result.returncode == 1
        assert "Error" in result.stderr
        assert "not found" in result.stderr.lower()

    def test_invalid_yaml_syntax(self, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("key: [\nbad yaml")
        result = _run(["validate", str(bad)])
        assert result.returncode == 1
        assert "Error" in result.stderr

    def test_missing_required_field(self, tmp_path):
        broken = tmp_path / "broken.yaml"
        broken.write_text(
            "transitions:\n"
            "  - name: TestTransition\n"
            "    entity_type: Order\n"
            "    from_state: A\n"
            # to_state missing
        )
        result = _run(["validate", str(broken)])
        assert result.returncode == 1
        assert "Error" in result.stderr

    def test_invalid_constraint_rule(self, tmp_path):
        broken = tmp_path / "broken.yaml"
        broken.write_text(
            "transitions:\n"
            "  - name: T\n"
            "    entity_type: Order\n"
            "    from_state: A\n"
            "    to_state: B\n"
            "constraints:\n"
            "  - name: BadRule\n"
            "    applies_to: T\n"
            "    rule: days <= 7 && status == active\n"
        )
        result = _run(["validate", str(broken)])
        assert result.returncode == 1
        assert "Error" in result.stderr

    def test_world_name_fallback_to_stem(self, tmp_path):
        minimal = tmp_path / "my_world.yaml"
        minimal.write_text(
            "transitions:\n"
            "  - name: T\n"
            "    entity_type: Order\n"
            "    from_state: A\n"
            "    to_state: B\n"
        )
        result = _run(["validate", str(minimal)])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["world"] == "my_world"

    def test_no_subcommand_exits_nonzero(self):
        result = _run([])
        assert result.returncode == 1
