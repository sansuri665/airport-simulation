from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class SchemaValidationError(AssertionError):
    pass


def load_schema_registry(schema_root: Path) -> dict[str, dict[str, Any]]:
    import json

    registry: dict[str, dict[str, Any]] = {}
    for path in sorted(schema_root.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        registry[path.name] = schema
        schema_id = schema.get("$id")
        if isinstance(schema_id, str):
            registry[schema_id] = schema
    return registry


def resolve_pointer(document: Any, pointer: str) -> Any:
    if not pointer:
        return document
    if not pointer.startswith("/"):
        raise SchemaValidationError(f"unsupported JSON pointer: #{pointer}")
    current = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or part not in current:
            raise SchemaValidationError(f"unresolved JSON pointer: #{pointer}")
        current = current[part]
    return current


def resolve_ref(
    reference: str,
    current_name: str,
    registry: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    target_name, separator, fragment = reference.partition("#")
    target_name = target_name or current_name
    if target_name not in registry:
        target_name = target_name.rsplit("/", 1)[-1]
    if target_name not in registry:
        raise SchemaValidationError(f"unknown schema reference: {reference}")
    target_document = registry[target_name]
    target = resolve_pointer(target_document, fragment if separator else "")
    if not isinstance(target, dict):
        raise SchemaValidationError(f"schema reference is not an object: {reference}")
    return target, target_name


def matches_type(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    raise SchemaValidationError(f"unsupported schema type: {expected}")


def validate_schema(
    value: Any,
    schema: dict[str, Any],
    registry: dict[str, dict[str, Any]],
    *,
    current_name: str,
    path: str = "$",
) -> None:
    if "$ref" in schema:
        target, target_name = resolve_ref(str(schema["$ref"]), current_name, registry)
        validate_schema(value, target, registry, current_name=target_name, path=path)

    for index, part in enumerate(schema.get("allOf", [])):
        validate_schema(value, part, registry, current_name=current_name, path=f"{path}.allOf[{index}]")

    if "const" in schema and value != schema["const"]:
        raise SchemaValidationError(f"{path}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise SchemaValidationError(f"{path}: {value!r} is not in {schema['enum']!r}")

    expected_types = schema.get("type")
    if expected_types is not None:
        if isinstance(expected_types, str):
            expected_types = [expected_types]
        if not any(matches_type(value, expected) for expected in expected_types):
            raise SchemaValidationError(f"{path}: expected type {expected_types!r}, got {type(value).__name__}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            raise SchemaValidationError(f"{path}: missing required keys {missing!r}")
        minimum_properties = schema.get("minProperties")
        if minimum_properties is not None and len(value) < int(minimum_properties):
            raise SchemaValidationError(f"{path}: expected at least {minimum_properties} properties")
        properties = schema.get("properties", {})
        for key, child_schema in properties.items():
            if key in value:
                validate_schema(
                    value[key],
                    child_schema,
                    registry,
                    current_name=current_name,
                    path=f"{path}.{key}",
                )
        additional = schema.get("additionalProperties", True)
        unknown = [key for key in value if key not in properties]
        if additional is False and unknown:
            raise SchemaValidationError(f"{path}: unexpected keys {unknown!r}")
        if isinstance(additional, dict):
            for key in unknown:
                validate_schema(
                    value[key],
                    additional,
                    registry,
                    current_name=current_name,
                    path=f"{path}.{key}",
                )

    if isinstance(value, list):
        minimum_items = schema.get("minItems")
        if minimum_items is not None and len(value) < int(minimum_items):
            raise SchemaValidationError(f"{path}: expected at least {minimum_items} items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                validate_schema(
                    item,
                    item_schema,
                    registry,
                    current_name=current_name,
                    path=f"{path}[{index}]",
                )

    if isinstance(value, str):
        minimum_length = schema.get("minLength")
        if minimum_length is not None and len(value) < int(minimum_length):
            raise SchemaValidationError(f"{path}: string is shorter than {minimum_length}")
        pattern = schema.get("pattern")
        if pattern is not None and re.search(str(pattern), value) is None:
            raise SchemaValidationError(f"{path}: {value!r} does not match {pattern!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if minimum is not None and value < minimum:
            raise SchemaValidationError(f"{path}: {value!r} is less than {minimum!r}")


def validate_named_schema(
    value: Any,
    schema_name: str,
    registry: dict[str, dict[str, Any]],
) -> None:
    if schema_name not in registry:
        raise SchemaValidationError(f"schema is not registered: {schema_name}")
    validate_schema(value, registry[schema_name], registry, current_name=schema_name)
