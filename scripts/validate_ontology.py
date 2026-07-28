#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = ["pyyaml"]
# ///
"""Validate referential integrity of taxonomy YAML artifacts.

Checks that all entity references in relationships.yaml resolve to
entries defined in entities.yaml, and validates schema conformance.
"""

import os
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)


def load_yaml(filepath: Path) -> dict:
    """Load a YAML file, returning its content."""
    with open(filepath) as f:
        return yaml.safe_load(f)


def collect_entity_ids(entities: dict) -> set:
    """Collect all entity IDs from the entities structure."""
    ids = set()
    for category, items in entities.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "id" in item:
                    ids.add(item["id"])
    return ids


def validate():
    """Run all validation checks."""
    errors = []
    warnings = []

    tax_dir = REPO_ROOT / "taxonomy"

    # Check files exist
    for fname in ["entities.yaml", "relationships.yaml", "ontology.yaml"]:
        if not (tax_dir / fname).exists():
            errors.append(f"Missing file: taxonomy/{fname}")

    if errors:
        return errors, warnings

    # Load files
    entities = load_yaml(tax_dir / "entities.yaml")
    rel_data = load_yaml(tax_dir / "relationships.yaml")
    ontology = load_yaml(tax_dir / "ontology.yaml")

    # Collect all entity IDs
    all_ids = collect_entity_ids(entities)

    if not all_ids:
        errors.append("No entity IDs found in entities.yaml")
        return errors, warnings

    # Check required entity categories
    required_categories = [
        "skills", "domains", "organizations",
        "roles", "projects", "compliance",
        "patterns", "tags",
    ]
    for cat in required_categories:
        if cat not in entities:
            errors.append(f"Missing entity category: {cat}")
        elif not entities[cat]:
            warnings.append(f"Empty entity category: {cat}")

    # Validate relationships reference existing entities
    relationships = rel_data.get("relationships", [])
    if not relationships:
        errors.append("No relationships found")
        return errors, warnings

    for i, rel in enumerate(relationships):
        subj = rel.get("subject", "")
        obj = rel.get("object", "")
        predicate = rel.get("predicate", "")

        if not subj:
            errors.append(f"Relationship [{i}]: missing subject")
        elif subj not in all_ids:
            errors.append(f"Relationship [{i}]: subject '{subj}' not in entities")

        if not obj:
            errors.append(f"Relationship [{i}]: missing object")
        elif obj not in all_ids:
            errors.append(f"Relationship [{i}]: object '{obj}' not in entities")

        if not predicate:
            errors.append(f"Relationship [{i}]: missing predicate")

        # Validate context references
        context = rel.get("context", {})
        for key, value in context.items():
            if key in ("role", "project", "domain",
                       "organization", "compliance"):
                refs = value if isinstance(value, list) else [value]
                for ref in refs:
                    if isinstance(ref, str) and ref not in all_ids:
                        errors.append(
                            f"Relationship [{i}]: context.{key} "
                            f"'{ref}' not in entities"
                        )
            elif key == "co_skills":
                if isinstance(value, list):
                    for ref in value:
                        if ref not in all_ids:
                            errors.append(
                                f"Relationship [{i}]: "
                                f"co_skill '{ref}' not in entities"
                            )

    # Validate ontology schema has expected sections
    expected_sections = [
        "meta", "entity_types", "relationship_types",
        "context_dimensions",
    ]
    for section in expected_sections:
        if section not in ontology:
            errors.append(f"Ontology missing section: {section}")

    # Build entity-to-type mapping for type constraint checks
    entity_type_map = {}
    type_prefix_map = {}
    if "entity_types" in ontology:
        for type_name, type_def in ontology["entity_types"].items():
            prefix = type_def.get("id_prefix", "")
            type_prefix_map[prefix] = type_name

    for category, items in entities.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "id" in item:
                    eid = item["id"]
                    # Determine type from prefix
                    for prefix, type_name in type_prefix_map.items():
                        if eid.startswith(prefix):
                            entity_type_map[eid] = type_name
                            break

    # Validate relationship type constraints from ontology
    rel_types = ontology.get("relationship_types", {})
    for i, rel in enumerate(relationships):
        predicate = rel.get("predicate", "")
        subj = rel.get("subject", "")
        obj = rel.get("object", "")

        if predicate not in rel_types:
            continue  # Unknown predicate - already caught by other checks

        rel_schema = rel_types[predicate]
        subject_types = rel_schema.get("subject_types", [])
        object_types = rel_schema.get("object_types", [])

        # Check subject type constraint
        subj_type = entity_type_map.get(subj)
        if subj_type and subject_types and subj_type not in subject_types:
            errors.append(
                f"Relationship [{i}]: subject '{subj}' is type "
                f"'{subj_type}' but '{predicate}' requires "
                f"subject_types {subject_types}"
            )

        # Check object type constraint
        obj_type = entity_type_map.get(obj)
        if obj_type and object_types and obj_type not in object_types:
            errors.append(
                f"Relationship [{i}]: object '{obj}' is type "
                f"'{obj_type}' but '{predicate}' requires "
                f"object_types {object_types}"
            )

    # Check for orphan entities (not referenced in any relationship)
    referenced_ids = set()
    for rel in relationships:
        referenced_ids.add(rel.get("subject", ""))
        referenced_ids.add(rel.get("object", ""))
        ctx = rel.get("context", {})
        for v in ctx.values():
            if isinstance(v, str):
                referenced_ids.add(v)
            elif isinstance(v, list):
                referenced_ids.update(
                    x for x in v if isinstance(x, str)
                )

    orphans = all_ids - referenced_ids
    # Tags are allowed to be orphans (informational only)
    tag_ids = {
        e["id"] for e in entities.get("tags", [])
        if isinstance(e, dict)
    }
    non_tag_orphans = orphans - tag_ids
    if non_tag_orphans:
        for oid in sorted(non_tag_orphans):
            warnings.append(f"Orphan entity (not referenced): {oid}")

    return errors, warnings


def main():
    """Run validation and report results."""
    print("Validating taxonomy ontology integrity...")

    errors, warnings = validate()

    if warnings:
        print(f"\n  Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"    WARN: {w}")

    if errors:
        print(f"\n  Errors ({len(errors)}):")
        for e in errors:
            print(f"    ERROR: {e}")
        print(f"\nValidation FAILED with {len(errors)} error(s).")
        return 1

    print("\n  All checks passed.")
    print(f"  {len(warnings)} warning(s), 0 error(s).")
    print("\nValidation PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
