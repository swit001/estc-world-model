from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .loader import load_world_from_yaml
from .parser import RuleParseError


def _world_name(data: dict, path: Path) -> str:
    """Extract world name from YAML data, fallback to file stem."""
    world_block = data.get("world")
    if isinstance(world_block, dict):
        name = world_block.get("name")
        if name:
            return str(name)
    return path.stem


def cmd_schema(args: argparse.Namespace) -> int:
    from .schema import verdict_schema, world_schema

    if args.all:
        w = world_schema()
        v = verdict_schema()
        if args.out:
            out_dir = Path(args.out)
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "world.schema.json").write_text(
                json.dumps(w, indent=2), encoding="utf-8"
            )
            (out_dir / "verdict.schema.json").write_text(
                json.dumps(v, indent=2), encoding="utf-8"
            )
        else:
            print(json.dumps({"world": w, "verdict": v}, indent=2))
    elif args.verdict:
        schema = verdict_schema()
        if args.out:
            Path(args.out).write_text(json.dumps(schema, indent=2), encoding="utf-8")
        else:
            print(json.dumps(schema, indent=2))
    else:
        schema = world_schema()
        if args.out:
            Path(args.out).write_text(json.dumps(schema, indent=2), encoding="utf-8")
        else:
            print(json.dumps(schema, indent=2))

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    path = Path(args.file)

    # 1. File existence
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    # 2. YAML parsing
    try:
        with path.open(encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        print(f"Error: Invalid YAML: {exc}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        print("Error: World file must be a YAML mapping.", file=sys.stderr)
        return 1

    world_name = _world_name(data, path)

    # 3. Structure + rule validation via loader
    try:
        world = load_world_from_yaml(path)
    except (ValueError, RuleParseError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = {
        "valid": True,
        "world": world_name,
        "entities": 0,
        "transitions": len(world.transitions),
        "constraints": len(world.constraints),
    }
    print(json.dumps(result))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="estc",
        description="ESTC world model CLI",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="command")

    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate a declarative ESTC world definition.",
    )
    validate_parser.add_argument("file", help="Path to a .world.yaml or .yaml file.")

    schema_parser = subparsers.add_parser(
        "schema",
        help="Export JSON Schema for world definitions or VerdictOutcome.",
    )
    schema_parser.add_argument(
        "--verdict",
        action="store_true",
        help="Export the VerdictOutcome runtime contract schema.",
    )
    schema_parser.add_argument(
        "--all",
        action="store_true",
        help="Export both world and verdict schemas.",
    )
    schema_parser.add_argument(
        "--out",
        metavar="PATH",
        help="Write schema to file, or directory when using --all.",
    )

    args = parser.parse_args()

    if args.command == "validate":
        sys.exit(cmd_validate(args))
    elif args.command == "schema":
        sys.exit(cmd_schema(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
