#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.13"
# dependencies = ["pyyaml"]
# ///
"""Check ontology coverage against reference documents.

Analyzes whether the taxonomy entities and relationships adequately
cover the technologies, companies, roles, standards, and other terms
mentioned in the reference CV documents.

Reports:
  1. Terms mentioned in references but missing from entities.yaml
  2. Entity pairs co-occurring in reference text with no relationship
  3. Coverage metrics (% of reference terms captured)
  4. Relationship factual consistency vs reference text
  5. Potential orphan entities (in taxonomy but not grounded in refs)
"""

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)


# ---------------------------------------------------------------------------
# Term extraction from reference documents
# ---------------------------------------------------------------------------

# Known terms to look for in reference docs, grouped by category.
# This is a curated list derived from patterns typically found in CV/profile docs.
TECHNOLOGY_TERMS = {
    # Languages
    "Python", "JavaScript", "TypeScript", "Shell", "Bash", "C", "C++",
    "PL/SQL", "HTML", "CSS",
    # Frameworks
    "FastAPI", "Django", "React", "Redux", "React Native", "VueJS", "NuxtJS",
    "RiotJS", "GraphQL", "Serverless Framework", "Celery",
    # AWS Services
    "AWS", "AWS Lambda", "Lambda", "DynamoDB", "AWS DynamoDB", "SQS", "AWS SQS",
    "EventBridge", "AWS EventBridge", "Kinesis", "AWS Kinesis",
    "S3", "AWS S3", "API Gateway", "AWS API Gateway",
    "Athena", "AWS Athena", "Timestream", "AWS Timestream",
    "RedShift", "AWS RedShift", "AppSync", "AWS AppSync",
    "GovCloud", "AWS GovCloud", "X-Ray", "AWS X-Ray",
    "CloudWatch", "AWS CloudWatch", "Powertools", "AWS Powertools",
    # Other Platforms
    "Azure", "Digital Ocean", "CloudFlare",
    # Tools
    "Kubernetes", "Docker", "Terraform", "SaltStack", "Ansible",
    "GitHub Actions", "CircleCI", "ArgoCD", "Jenkins", "Git",
    "DataDog", "Prometheus", "LogicMonitor", "ThousandEyes",
    "ReportLab", "Typst", "MistQL", "CycloneDX", "SPDX",
    "Apache Kafka", "Kafka", "RabbitMQ", "Asterisk PBX", "Asterisk",
    "Ceph", "GDAL/OGR", "GDAL", "SnapCraft", "Ubuntu Core", "iPXE",
    # Libraries
    "OpenTelemetry", "JSON Patch",
    # Protocols/Standards
    "SNMP", "SIP/IAX", "SIP", "IAX", "SMTP", "HL7/FHIR", "HL7", "FHIR",
    "DICOM", "Twilio",
    # Databases
    "PostgreSQL", "PostGIS", "SnowflakeDB", "Snowflake", "MongoDB",
    "Redis", "Intersystems IRIS", "IRIS/Cache", "Oracle",
    # Methodologies
    "Prompt Engineering", "CI/CD", "Infrastructure as Code", "IaC",
    "DevSecOps", "Penetration Testing", "Dependency Scanning",
    "Synthetic Data Generation", "Machine Learning",
    # AI-specific
    "Claude", "Cursor", "LLM", "Large Language Models",
    # Compliance
    "HIPAA", "CMS", "Medicare", "Medicaid", "HL7/FHIR", "SOC I/II",
    "SOC", "OWASP", "FedRAMP", "Zero-Trust", "BeyondCorp", "Secure Boot",
    "SBOM",
    # Design Patterns
    "Clean Architecture", "Domain-Driven Design", "DDD",
    "Event-Driven Architecture", "Microservice", "Serverless Architecture",
    "Asynchronous Process Design", "Shift-Left",
    "Zero-Trust Architecture", "Platform as a Service", "PaaS",
    "Predictive Analytics", "Distributed Tracing",
    # Misc
    "VOD", "Video on Demand",
}

ORGANIZATION_TERMS = {
    "Arine", "Brute Technologies", "Adobe", "TekSystems",
    "Capital Group", "Insight Global", "Department of Veteran Affairs",
    "DocMe360", "Serverless", "Taos", "IBM Consulting", "IBM",
    "Metify", "EveryoneSocial", "Gravit", "CGI", "AT&T", "ABR",
    "Microcom", "Sateo", "Gardyn", "Slack", "Stripe",
    "NASA", "USGS", "Fortune-500",
}

DOMAIN_TERMS = {
    "Healthcare", "Federal", "Government", "Telecommunications", "Telecom",
    "IoT", "Industrial", "Security", "Cybersecurity", "GIS", "Geospatial",
    "Advertising", "Media", "Ag-Tech", "Finance", "Enterprise",
    "SaaS", "Telemedicine", "Observability", "Edge Computing",
    "Data Engineering", "Clinical",
}


def load_yaml_file(filepath: Path) -> dict:
    """Load a YAML file."""
    with open(filepath) as f:
        return yaml.safe_load(f)


def read_reference_texts() -> dict[str, str]:
    """Read all reference markdown files and return name->content mapping."""
    ref_dir = REPO_ROOT / "reference"
    texts = {}
    for md_file in sorted(ref_dir.glob("*.md")):
        texts[md_file.name] = md_file.read_text()
    return texts


def extract_mentioned_terms(text: str, term_set: set[str]) -> set[str]:
    """Find which terms from term_set appear in the text (case-insensitive where appropriate)."""
    found = set()
    for term in term_set:
        # For short terms (<=3 chars), require word boundaries and case sensitivity
        if len(term) <= 3:
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text):
                found.add(term)
        else:
            # Case-insensitive search with word boundaries for longer terms
            pattern = r'\b' + re.escape(term) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found.add(term)
    return found


def collect_entity_names(entities: dict) -> dict[str, set[str]]:
    """Collect entity names by category."""
    result = {}
    for category, items in entities.items():
        if isinstance(items, list):
            result[category] = set()
            for item in items:
                if isinstance(item, dict) and "name" in item:
                    result[category].add(item["name"])
    return result


def collect_entity_ids(entities: dict) -> set[str]:
    """Collect all entity IDs."""
    ids = set()
    for category, items in entities.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "id" in item:
                    ids.add(item["id"])
    return ids


def collect_entity_id_to_name(entities: dict) -> dict[str, str]:
    """Map entity IDs to names."""
    mapping = {}
    for category, items in entities.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "id" in item:
                    mapping[item["id"]] = item.get("name", item["id"])
    return mapping


def normalize_term(term: str) -> str:
    """Normalize a term for comparison."""
    return re.sub(r'[^a-z0-9]+', '', term.lower().strip())


def build_entity_name_lookup(entities: dict) -> dict[str, str]:
    """Build a normalized-name -> entity-id lookup."""
    lookup = {}
    for category, items in entities.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "name" in item:
                    norm = normalize_term(item["name"])
                    lookup[norm] = item["id"]
                    # Also index by id for direct matches
                    lookup[normalize_term(item["id"])] = item["id"]
    return lookup


# Aliases that map reference terms to entity names
TERM_ALIASES = {
    "Lambda": "AWS Lambda",
    "DynamoDB": "AWS DynamoDB",
    "SQS": "AWS SQS",
    "EventBridge": "AWS EventBridge",
    "Kinesis": "AWS Kinesis",
    "S3": "AWS S3",
    "API Gateway": "AWS API Gateway",
    "Athena": "AWS Athena",
    "Timestream": "AWS Timestream",
    "RedShift": "AWS RedShift",
    "AppSync": "AWS AppSync",
    "GovCloud": "AWS GovCloud",
    "X-Ray": "AWS X-Ray",
    "CloudWatch": "AWS CloudWatch",
    "Powertools": "AWS Powertools",
    "Kafka": "Apache Kafka",
    "Asterisk": "Asterisk PBX",
    "IaC": "Infrastructure as Code",
    "DDD": "Domain-Driven Design",
    "Snowflake": "SnowflakeDB",
    "IRIS/Cache": "Intersystems IRIS/Cache",
    "Intersystems IRIS": "Intersystems IRIS/Cache",
    "PaaS": "Platform as a Service",
    "Bash": "Shell",
    "Microservice": "Microservice Architecture",
    "Telecom": "Telecommunications",
    "GDAL": "GDAL/OGR",
    "SIP": "SIP/IAX",
    "IAX": "SIP/IAX",
    "HL7": "HL7/FHIR",
    "FHIR": "HL7/FHIR",
    "BeyondCorp": "Zero-Trust/BeyondCorp",
    "Zero-Trust": "Zero-Trust/BeyondCorp",
    "Medicare": "Medicare/Medicaid",
    "Medicaid": "Medicare/Medicaid",
    "SOC": "SOC I/II",
    "SBOM": "SBOM Standards",
    "Shift-Left": "Shift-Left Security",
    "LLM": "Prompt Engineering",
    "Large Language Models": "Prompt Engineering",
    "Claude": "Prompt Engineering",
    "Cursor": "Prompt Engineering",
    "VOD": "Advertising/Media",
    "Video on Demand": "Advertising/Media",
    "Gravit": "EveryoneSocial",
    "HTML": "JavaScript",
    "CSS": "JavaScript",
    # Domain aliases
    "Federal": "Federal/Government",
    "Government": "Federal/Government",
    "IoT": "IoT/Industrial",
    "Industrial": "IoT/Industrial",
    "GIS": "GIS/Geospatial",
    "Geospatial": "GIS/Geospatial",
    "Advertising": "Advertising/Media",
    "Media": "Advertising/Media",
    "Enterprise": "Finance/Enterprise",
    "SaaS": "SaaS/Product",
    "Cybersecurity": "Security",
    "Clinical": "Healthcare",
}


def check_term_coverage(ref_texts: dict[str, str], entities: dict) -> dict:
    """Check which reference terms are covered by entities."""
    all_entity_names = set()
    for category, items in entities.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "name" in item:
                    all_entity_names.add(item["name"])

    # Combine all reference text
    combined_text = "\n".join(ref_texts.values())

    # Find all technology terms mentioned
    tech_mentioned = extract_mentioned_terms(combined_text, TECHNOLOGY_TERMS)
    org_mentioned = extract_mentioned_terms(combined_text, ORGANIZATION_TERMS)
    domain_mentioned = extract_mentioned_terms(combined_text, DOMAIN_TERMS)

    # Resolve aliases
    def resolve(term):
        return TERM_ALIASES.get(term, term)

    # Check coverage
    tech_covered = set()
    tech_missing = set()
    for term in tech_mentioned:
        resolved = resolve(term)
        norm_resolved = normalize_term(resolved)
        found = False
        for name in all_entity_names:
            if normalize_term(name) == norm_resolved:
                found = True
                break
        if found:
            tech_covered.add(term)
        else:
            # Check if this is just an alias of something already covered
            if resolved != term:
                for name in all_entity_names:
                    if normalize_term(name) == normalize_term(resolved):
                        found = True
                        break
            if not found:
                tech_missing.add(term)

    org_covered = set()
    org_missing = set()
    for term in org_mentioned:
        resolved = resolve(term)
        norm_resolved = normalize_term(resolved)
        found = False
        for name in all_entity_names:
            if normalize_term(name) == norm_resolved:
                found = True
                break
        if found:
            org_covered.add(term)
        else:
            org_missing.add(term)

    domain_covered = set()
    domain_missing = set()
    for term in domain_mentioned:
        resolved = resolve(term)
        norm_resolved = normalize_term(resolved)
        found = False
        for name in all_entity_names:
            if normalize_term(name) == norm_resolved:
                found = True
                break
        if found:
            domain_covered.add(term)
        else:
            domain_missing.add(term)

    return {
        "technology": {
            "mentioned": tech_mentioned,
            "covered": tech_covered,
            "missing": tech_missing,
        },
        "organizations": {
            "mentioned": org_mentioned,
            "covered": org_covered,
            "missing": org_missing,
        },
        "domains": {
            "mentioned": domain_mentioned,
            "covered": domain_covered,
            "missing": domain_missing,
        },
    }


def check_relationship_coverage(
    ref_texts: dict[str, str],
    entities: dict,
    relationships: list[dict],
) -> dict:
    """Check if entity pairs that co-occur in reference text have relationships."""
    # Build entity name -> id mapping
    name_to_id = {}
    for category, items in entities.items():
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict) and "name" in item and "id" in item:
                    name_to_id[item["name"]] = item["id"]

    # Build set of related pairs (both directions)
    related_pairs = set()
    for rel in relationships:
        subj = rel.get("subject", "")
        obj = rel.get("object", "")
        related_pairs.add((subj, obj))
        related_pairs.add((obj, subj))
        # Also capture context references
        ctx = rel.get("context", {})
        for v in ctx.values():
            if isinstance(v, str) and v in name_to_id.values():
                related_pairs.add((subj, v))
                related_pairs.add((v, subj))
                related_pairs.add((obj, v))
                related_pairs.add((v, obj))
            elif isinstance(v, list):
                for ref in v:
                    if isinstance(ref, str):
                        related_pairs.add((subj, ref))
                        related_pairs.add((ref, subj))
                        related_pairs.add((obj, ref))
                        related_pairs.add((ref, obj))

    # For each reference section (paragraph/block), find co-occurring entities
    combined = "\n".join(ref_texts.values())
    # Split into meaningful sections (paragraphs or role blocks)
    sections = re.split(r'\n\n+', combined)

    missing_relationships = []
    checked_pairs = set()

    # Focus on skill-to-organization and skill-to-project co-occurrences
    org_names = {item["name"]: item["id"] for item in entities.get("organizations", []) if isinstance(item, dict)}
    skill_names = {item["name"]: item["id"] for item in entities.get("skills", []) if isinstance(item, dict)}
    project_names = {item["name"]: item["id"] for item in entities.get("projects", []) if isinstance(item, dict)}

    # Filter out very short or ambiguous skill names that produce false co-occurrences
    # (e.g., "C" matches many contexts, "Git" matches inside "Digital")
    filtered_skill_names = {
        name: eid for name, eid in skill_names.items()
        if len(name) > 2 and name not in ("Git",)
    }

    for section in sections:
        if len(section.strip()) < 50:
            continue

        # Find orgs mentioned in this section
        orgs_in_section = set()
        for name, eid in org_names.items():
            if len(name) > 3:
                if re.search(r'\b' + re.escape(name) + r'\b', section, re.IGNORECASE):
                    orgs_in_section.add(eid)

        # Find skills mentioned in this section
        skills_in_section = set()
        for name, eid in filtered_skill_names.items():
            if len(name) > 3:
                if re.search(r'\b' + re.escape(name) + r'\b', section, re.IGNORECASE):
                    skills_in_section.add(eid)
            elif name in section:
                skills_in_section.add(eid)

        # Check skill-org pairs
        for skill_id in skills_in_section:
            for org_id in orgs_in_section:
                pair = (skill_id, org_id)
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                # Check if there's any relationship connecting these
                if pair not in related_pairs and (org_id, skill_id) not in related_pairs:
                    missing_relationships.append({
                        "skill": skill_id,
                        "organization": org_id,
                        "type": "skill_at_org_no_relationship",
                    })

    return {
        "missing_relationships": missing_relationships,
        "total_pairs_checked": len(checked_pairs),
    }


def check_relationship_factual_consistency(
    ref_texts: dict[str, str],
    entities: dict,
    relationships: list[dict],
) -> list[dict]:
    """Verify relationships make factual sense vs reference documents."""
    issues = []
    id_to_name = collect_entity_id_to_name(entities)
    combined = "\n".join(ref_texts.values())

    # Check held_role_at relationships match what's in the references
    for rel in relationships:
        if rel.get("predicate") != "held_role_at":
            continue
        role_id = rel.get("subject", "")
        org_id = rel.get("object", "")
        role_name = id_to_name.get(role_id, role_id)
        org_name = id_to_name.get(org_id, org_id)

        # Check org is mentioned in refs
        if len(org_name) > 3:
            if not re.search(r'\b' + re.escape(org_name) + r'\b', combined, re.IGNORECASE):
                issues.append({
                    "relationship": f"{role_name} -> held_role_at -> {org_name}",
                    "issue": f"Organization '{org_name}' not found in reference documents",
                    "severity": "warning",
                })

    # Build skill name aliases for flexible matching
    # e.g., "AWS DynamoDB" should also match "DynamoDB"
    def get_skill_search_terms(name: str) -> list[str]:
        """Get all search terms for a skill name (including aliases)."""
        terms = [name]
        # Strip common prefixes
        if name.startswith("AWS "):
            terms.append(name[4:])
        # Handle slash-separated names
        if "/" in name:
            terms.extend(p.strip() for p in name.split("/"))
        # Handle common reformulations
        reformulations = {
            "Infrastructure as Code": ["Infrastructure-as-Code", "IaC"],
            "Domain-Driven Design": ["DDD"],
            "CI/CD": ["CI/CD", "Continuous Integration"],
            "Shift-Left Security": ["Shift-Left"],
        }
        if name in reformulations:
            terms.extend(reformulations[name])
        return terms

    # Check applied_in_project: verify skill is actually mentioned in same context as project's org
    sections = re.split(r'\n\n+', combined)
    for rel in relationships:
        if rel.get("predicate") != "applied_in_project":
            continue
        skill_id = rel.get("subject", "")
        project_id = rel.get("object", "")
        ctx = rel.get("context", {})
        org_id = ctx.get("organization", "")

        skill_name = id_to_name.get(skill_id, skill_id)
        project_name = id_to_name.get(project_id, project_id)
        org_name = id_to_name.get(org_id, org_id)

        if not org_name or len(org_name) <= 3:
            continue

        # Find sections mentioning the org
        org_sections = [s for s in sections if re.search(r'\b' + re.escape(org_name) + r'\b', s, re.IGNORECASE)]

        if org_sections:
            # Check if skill (or any of its aliases) is mentioned near the org
            search_terms = get_skill_search_terms(skill_name)
            skill_found = False
            for section in org_sections:
                for term in search_terms:
                    if len(term) <= 3:
                        if term in section:
                            skill_found = True
                            break
                    else:
                        if re.search(r'\b' + re.escape(term) + r'\b', section, re.IGNORECASE):
                            skill_found = True
                            break
                if skill_found:
                    break
            if not skill_found:
                # Not necessarily wrong -- skill might be implied or in nearby text
                # Only flag if skill (or aliases) isn't mentioned ANYWHERE in the refs
                anywhere_found = False
                for term in search_terms:
                    if len(term) > 3:
                        if re.search(r'\b' + re.escape(term) + r'\b', combined, re.IGNORECASE):
                            anywhere_found = True
                            break
                    else:
                        if term in combined:
                            anywhere_found = True
                            break
                if not anywhere_found:
                    issues.append({
                        "relationship": f"{skill_name} -> applied_in_project -> {project_name}",
                        "issue": f"Skill '{skill_name}' not found anywhere in reference documents",
                        "severity": "error",
                    })

    return issues


def find_orphan_entities(entities: dict, ref_texts: dict[str, str]) -> list[dict]:
    """Find entities in taxonomy that aren't grounded in reference documents."""
    combined = "\n".join(ref_texts.values())
    orphans = []

    def name_in_text(name: str, text: str) -> bool:
        """Check if a name (or its aliases) appears in text."""
        # Direct match
        if len(name) <= 3:
            if name in text:
                return True
        else:
            if re.search(r'\b' + re.escape(name) + r'\b', text, re.IGNORECASE):
                return True

        # Check common aliases / substrings
        aliases_to_check = []
        if name.startswith("AWS "):
            aliases_to_check.append(name[4:])
        if "/" in name:
            aliases_to_check.extend(p.strip() for p in name.split("/"))
        # Hyphenated reformulations
        reformulations = {
            "Infrastructure as Code": ["Infrastructure-as-Code", "IaC"],
            "Platform as a Service": ["Platform-as-a-Service", "PaaS"],
            "Microservice Architecture": ["Microservice", "Microservices"],
            "Edge-Optimized Architecture": ["edge-optimized"],
            "Shift-Left Security": ["Shift-Left"],
            "SBOM Standards": ["SBOM", "Software Bill of Materials"],
        }
        if name in reformulations:
            aliases_to_check.extend(reformulations[name])

        for alias in aliases_to_check:
            alias = alias.strip()
            if not alias:
                continue
            if len(alias) <= 3:
                if alias in text:
                    return True
            else:
                if re.search(r'\b' + re.escape(alias) + r'\b', text, re.IGNORECASE):
                    return True

        return False

    for category, items in entities.items():
        if not isinstance(items, list):
            continue
        # Skip tags - they are derived from pipe-delimited lines and always present
        if category == "tags":
            continue
        # Skip projects and roles - these have synthetic descriptive names
        # created by the extraction script, not literal text from docs.
        # Their grounding is validated through relationship integrity instead.
        if category in ("projects", "roles"):
            continue
        for item in items:
            if not isinstance(item, dict) or "name" not in item:
                continue
            name = item["name"]
            eid = item.get("id", "")

            if not name_in_text(name, combined):
                orphans.append({
                    "id": eid,
                    "name": name,
                    "category": category,
                })

    return orphans


def print_report(coverage: dict, rel_coverage: dict, factual_issues: list, orphans: list):
    """Print a comprehensive coverage report."""
    print("=" * 72)
    print("  ONTOLOGY COVERAGE ANALYSIS REPORT")
    print("=" * 72)

    # --- Section 1: Term Coverage ---
    print("\n" + "-" * 72)
    print("  1. TERM COVERAGE (Reference Terms vs Entities)")
    print("-" * 72)

    total_mentioned = 0
    total_covered = 0

    for category, data in coverage.items():
        mentioned = len(data["mentioned"])
        covered = len(data["covered"])
        missing = len(data["missing"])
        total_mentioned += mentioned
        total_covered += covered
        pct = (covered / mentioned * 100) if mentioned > 0 else 0

        print(f"\n  [{category.upper()}]")
        print(f"    Mentioned in refs: {mentioned}")
        print(f"    Covered by taxonomy: {covered} ({pct:.1f}%)")
        if data["missing"]:
            print(f"    MISSING ({missing}):")
            for term in sorted(data["missing"]):
                print(f"      - {term}")

    overall_pct = (total_covered / total_mentioned * 100) if total_mentioned > 0 else 0
    print(f"\n  OVERALL: {total_covered}/{total_mentioned} terms covered ({overall_pct:.1f}%)")

    # --- Section 2: Relationship Coverage ---
    print("\n" + "-" * 72)
    print("  2. RELATIONSHIP COVERAGE (Co-occurring Entities Without Relationships)")
    print("-" * 72)

    missing_rels = rel_coverage["missing_relationships"]
    print(f"\n  Entity pairs checked: {rel_coverage['total_pairs_checked']}")
    print(f"  Pairs with relationships: {rel_coverage['total_pairs_checked'] - len(missing_rels)}")
    print(f"  Pairs WITHOUT relationships: {len(missing_rels)}")

    if missing_rels:
        rel_pct = ((rel_coverage['total_pairs_checked'] - len(missing_rels)) / rel_coverage['total_pairs_checked'] * 100) if rel_coverage['total_pairs_checked'] > 0 else 0
        print(f"  Relationship coverage: {rel_pct:.1f}%")
        print(f"\n  NOTE: Many 'missing' pairs are expected. The taxonomy stores")
        print(f"  relationships against end-clients (e.g., Adobe) rather than staffing")
        print(f"  firms (e.g., TekSystems) that appear as co-mentions in reference text.")
        print(f"\n  Top missing relationships (showing up to 20):")
        for item in missing_rels[:20]:
            print(f"    - {item['skill']} <-> {item['organization']}")
    else:
        print("  All co-occurring entity pairs have relationships!")

    # --- Section 3: Factual Consistency ---
    print("\n" + "-" * 72)
    print("  3. FACTUAL CONSISTENCY (Relationships vs Reference Text)")
    print("-" * 72)

    errors = [i for i in factual_issues if i["severity"] == "error"]
    warnings = [i for i in factual_issues if i["severity"] == "warning"]

    print(f"\n  Errors: {len(errors)}")
    print(f"  Warnings: {len(warnings)}")

    if errors:
        print("\n  ERRORS (relationship references something not in docs):")
        for issue in errors:
            print(f"    - {issue['relationship']}")
            print(f"      {issue['issue']}")

    if warnings:
        print(f"\n  WARNINGS (showing up to 10):")
        for issue in warnings[:10]:
            print(f"    - {issue['relationship']}")
            print(f"      {issue['issue']}")

    # --- Section 4: Orphan Entities ---
    print("\n" + "-" * 72)
    print("  4. POTENTIAL ORPHAN ENTITIES (In Taxonomy But Not in References)")
    print("-" * 72)

    if orphans:
        print(f"\n  Found {len(orphans)} entities not clearly grounded in reference text:")
        by_category = defaultdict(list)
        for o in orphans:
            by_category[o["category"]].append(o)
        for cat in sorted(by_category):
            print(f"\n    [{cat}]")
            for o in sorted(by_category[cat], key=lambda x: x["name"]):
                print(f"      - {o['name']} ({o['id']})")
    else:
        print("\n  All taxonomy entities are grounded in reference documents.")

    # --- Section 5: Summary ---
    print("\n" + "-" * 72)
    print("  5. SUMMARY")
    print("-" * 72)

    print(f"\n  Term Coverage:         {overall_pct:.1f}%")
    if rel_coverage['total_pairs_checked'] > 0:
        rel_pct = ((rel_coverage['total_pairs_checked'] - len(missing_rels)) / rel_coverage['total_pairs_checked'] * 100)
        print(f"  Relationship Coverage: {rel_pct:.1f}%")
    print(f"  Factual Errors:        {len(errors)}")
    print(f"  Factual Warnings:      {len(warnings)}")
    print(f"  Orphan Entities:       {len(orphans)}")

    # Overall assessment
    print("\n  ASSESSMENT:", end=" ")
    if overall_pct >= 90 and len(errors) == 0:
        print("EXCELLENT - Taxonomy has strong coverage of reference documents")
    elif overall_pct >= 75 and len(errors) <= 2:
        print("GOOD - Taxonomy covers most reference content with minor gaps")
    elif overall_pct >= 60:
        print("FAIR - Taxonomy has notable gaps that should be addressed")
    else:
        print("NEEDS WORK - Significant coverage gaps exist")

    print("\n" + "=" * 72)

    return len(errors)


def main():
    """Run coverage analysis."""
    tax_dir = REPO_ROOT / "taxonomy"

    # Load taxonomy
    entities = load_yaml_file(tax_dir / "entities.yaml")
    rel_data = load_yaml_file(tax_dir / "relationships.yaml")
    relationships = rel_data.get("relationships", [])

    # Load reference texts
    ref_texts = read_reference_texts()

    if not ref_texts:
        print("ERROR: No reference documents found in reference/")
        return 1

    print(f"Analyzing {len(ref_texts)} reference document(s) against taxonomy...")
    print(f"  Entities: {sum(len(v) for v in entities.values() if isinstance(v, list))}")
    print(f"  Relationships: {len(relationships)}")
    print()

    # Run analyses
    coverage = check_term_coverage(ref_texts, entities)
    rel_coverage = check_relationship_coverage(ref_texts, entities, relationships)
    factual_issues = check_relationship_factual_consistency(ref_texts, entities, relationships)
    orphans = find_orphan_entities(entities, ref_texts)

    # Print report
    error_count = print_report(coverage, rel_coverage, factual_issues, orphans)

    return 1 if error_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
